import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import create_app, MAX_UPLOAD_BYTES
from app.rag.retriever import Retriever
from app.rag.embeddings import Embedder
from app.rag.vector_store import VectorStore
from app.agent.core import AgentCore
from app.frameworks.langgraph.agent import LangGraphAgent
from app.frameworks.llamaindex.agent import LlamaIndexAgent

FIXTURE_PDF = Path(__file__).parent.parent / "rag" / "fixtures" / "sample.pdf"


@pytest.fixture(scope="module")
def embedder():
    # real fastembed embedder (model is cached locally); shared to keep tests fast
    return Embedder()


@pytest.fixture
def client(tmp_path, embedder):
    # one real retriever with an isolated in-memory Qdrant collection, shared by all agents
    store = VectorStore(dim=embedder.dim, collection="upload_test")
    retriever = Retriever(embedder=embedder, store=store)
    agents = {
        "core": AgentCore(retriever=retriever),
        "langgraph": LangGraphAgent(retriever=retriever),
        "llamaindex": LlamaIndexAgent(retriever=retriever),
    }
    app = create_app(
        agents=agents,
        retriever=retriever,
        db_path=str(tmp_path / "upload.db"),
        upload_dir=str(tmp_path / "uploads"),
    )
    return TestClient(app)


def _upload(client, filename, content, content_type):
    return client.post(
        "/documents/upload",
        files={"file": (filename, io.BytesIO(content), content_type)},
    )


def test_upload_pdf(client):
    r = _upload(client, "sample.pdf", FIXTURE_PDF.read_bytes(), "application/pdf")
    assert r.status_code == 200
    body = r.json()
    assert body["filename"] == "sample.pdf"
    assert body["status"] == "success"
    assert body["chunks_indexed"] >= 1


def test_upload_txt(client):
    r = _upload(client, "notes.txt", b"Mercury is the smallest planet.", "text/plain")
    assert r.status_code == 200
    assert r.json()["chunks_indexed"] >= 1


def test_upload_md(client):
    r = _upload(client, "readme.md", b"# Title\n\nSaturn has prominent rings.", "text/markdown")
    assert r.status_code == 200
    assert r.json()["chunks_indexed"] >= 1


def test_unsupported_extension_rejected(client):
    r = _upload(client, "evil.exe", b"MZ binary", "application/octet-stream")
    assert r.status_code == 400
    assert "unsupported file type" in r.json()["detail"]


def test_empty_file_rejected(client):
    r = _upload(client, "empty.txt", b"", "text/plain")
    assert r.status_code == 400
    assert "empty" in r.json()["detail"]


def test_oversized_file_rejected(client):
    big = b"a" * (MAX_UPLOAD_BYTES + 1)
    r = _upload(client, "big.txt", big, "text/plain")
    assert r.status_code == 400
    assert "too large" in r.json()["detail"]


def test_uploaded_document_is_retrievable_via_rag(client):
    _upload(client, "planets.txt", b"Jupiter is the largest planet in the solar system.", "text/plain")
    r = client.post("/query", json={"query": "Which is the largest planet?", "framework": "core"})
    assert r.status_code == 200
    body = r.json()
    assert body["tools_used"] == ["rag_search"]
    assert body["status"] == "success"
    sources = [e["source"] for e in body["evidence"]]
    assert "planets.txt" in sources
    assert any("Jupiter" in e["text"] for e in body["evidence"])


def test_document_listing(client):
    _upload(client, "a.txt", b"alpha content here", "text/plain")
    _upload(client, "b.md", b"beta content here", "text/markdown")
    r = client.get("/documents")
    assert r.status_code == 200
    docs = r.json()["documents"]
    assert "a.txt" in docs and "b.md" in docs


def test_path_traversal_filename_is_sanitized(client):
    r = _upload(client, "../../etc/passwd.txt", b"root:x:0:0", "text/plain")
    assert r.status_code == 200
    assert r.json()["filename"] == "passwd.txt"
    docs = client.get("/documents").json()["documents"]
    assert "passwd.txt" in docs
    assert not any(".." in d or "/" in d for d in docs)


def test_upload_error_does_not_expose_secrets(client):
    r = _upload(client, "evil.exe", b"x", "application/octet-stream")
    text = r.text.lower()
    assert "traceback" not in text
    assert "api_key" not in text and "qwen" not in text
