"""Streamlit demo UI for the Portable RAG Research Agent.

Talks to the FastAPI backend over HTTP so the UI stays framework-agnostic.
"""

import os

import httpx
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

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
                detail = up.json().get("detail", up.text) if up.content else up.text
                st.error(f"Upload failed ({up.status_code}): {detail}")
            else:
                d = up.json()
                st.success(f"Indexed {d['filename']}: {d['chunks_indexed']} chunk(s)")

    try:
        listing = httpx.get(f"{API_BASE_URL}/documents", timeout=15)
        docs = listing.json().get("documents", []) if listing.status_code == 200 else []
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
                detail = resp.json().get("detail", resp.text) if resp.content else resp.text
                st.error(f"API error {resp.status_code}: {detail}")
            else:
                data = resp.json()
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
