"""Streamlit demo UI for the Portable RAG Research Agent.

Talks to the FastAPI backend over HTTP so the UI stays framework-agnostic.
"""

import os

import httpx
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def _safe_json(resp: httpx.Response):
    """Return parsed JSON or None — never raises JSONDecodeError."""
    try:
        return resp.json()
    except Exception:
        return None


def _error_detail(resp: httpx.Response) -> str:
    """Extract a readable error message from any response, JSON or plain text."""
    data = _safe_json(resp)
    if data is not None and isinstance(data, dict):
        return data.get("detail", resp.text)
    return resp.text or f"HTTP {resp.status_code}"


st.set_page_config(page_title="Portable RAG Research Agent", page_icon="🔎")

st.title("Portable RAG Research Agent")
st.caption(
    "One agent contract, three orchestrators. The same request runs through "
    "**Core**, **LangGraph**, or **LlamaIndex** and returns the same response shape, "
    "evidence, and tool usage."
)

with st.sidebar:
    st.header("Knowledge Base")
    st.caption("Supported: PDF, TXT, MD")
    uploaded = st.file_uploader(
        "Choose a file", type=["pdf", "txt", "md"], accept_multiple_files=False
    )
    if st.button("Upload & Index") and uploaded is not None:
        try:
            up = httpx.post(
                f"{API_BASE_URL}/documents/upload",
                files={"file": (uploaded.name, uploaded.getvalue())},
                timeout=120,
            )
        except Exception as e:
            st.error(f"Could not reach the API at {API_BASE_URL}: {type(e).__name__}")
        else:
            if up.status_code != 200:
                st.error(f"Upload failed ({up.status_code}): {_error_detail(up)}")
            else:
                d = _safe_json(up)
                if d:
                    st.success(f"Indexed {d['filename']}: {d['chunks_indexed']} chunk(s)")
                else:
                    st.warning(f"Upload returned unexpected response: {up.text[:200]}")

    try:
        listing = httpx.get(f"{API_BASE_URL}/documents", timeout=15)
        listing_data = _safe_json(listing)
        docs = listing_data.get("documents", []) if listing_data and listing.status_code == 200 else []
    except Exception:
        docs = []
    if docs:
        st.subheader("Uploaded documents")
        for name in docs:
            st.write(f"- {name}")

framework = st.radio(
    "Framework", ["core", "langgraph", "llamaindex"], horizontal=True,
    help="Switch orchestrator and re-ask the same question to see portability.",
)

st.write("Try: *When is the project deadline?* · *What is 347 * 29?* · *What is the latest news?*")

query = st.text_area("Question", value="When is the project deadline?", height=80)

if st.button("Ask", type="primary"):
    if not query.strip():
        st.warning("Please enter a question.")
    else:
        try:
            resp = httpx.post(
                f"{API_BASE_URL}/query",
                json={"query": query.strip(), "framework": framework},
                timeout=120,
            )
        except Exception as e:
            st.error(f"Could not reach the API at {API_BASE_URL}: {type(e).__name__}")
        else:
            if resp.status_code != 200:
                st.error(f"API error {resp.status_code}: {_error_detail(resp)}")
            else:
                data = _safe_json(resp)
                if data is None:
                    st.error(f"API returned a non-JSON response: {resp.text[:200]}")
                else:
                    status = data.get("status")
                    (st.success if status == "success" else st.info)(f"Status: {status}")

                    st.subheader("Answer")
                    st.write(data.get("answer") or "_(no answer)_")

                    tools = data.get("tools_used") or []
                    st.subheader("Tools used")
                    st.write(", ".join(tools) if tools else "_(none)_")
                    if data.get("tool_calls"):
                        with st.expander("Tool calls"):
                            st.json(data["tool_calls"])

                    evidence = data.get("evidence") or []
                    st.subheader("Evidence")
                    if not evidence:
                        st.write("_(no evidence)_")
                    for e in evidence:
                        label = f"{e.get('source')}"
                        if e.get("page") is not None:
                            label += f" · page {e['page']}"
                        label += f" · {e.get('chunk_id')}"
                        with st.expander(label):
                            st.write(e.get("text"))

                    st.caption(f"Served by: {data.get('framework')}")
