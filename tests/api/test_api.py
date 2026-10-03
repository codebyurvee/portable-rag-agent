import sqlite3

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from app.agent.core import AgentCore
from app.frameworks.langgraph.agent import LangGraphAgent
from app.frameworks.llamaindex.agent import LlamaIndexAgent


class FakeRetriever:
    def __init__(self, hits):
        self._hits = hits

    def retrieve(self, query, top_k=4):
        return self._hits[:top_k]


DOC_HITS = [
    {"source": "rules.pdf", "page": 4, "chunk_id": "rules.pdf:4:0",
     "text": "The project deadline is October 3 2026."},
]


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "api_test.db")


@pytest.fixture
def client(db_path):
    retriever = FakeRetriever(DOC_HITS)
    agents = {
        "core": AgentCore(retriever=retriever),
        "langgraph": LangGraphAgent(retriever=retriever),
        "llamaindex": LlamaIndexAgent(retriever=retriever),
    }
    return TestClient(create_app(agents=agents, db_path=db_path))


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_query_default_framework(client):
    r = client.post("/query", json={"query": "When is the project deadline?"})
    assert r.status_code == 200
    body = r.json()
    assert body["framework"] == "core"
    assert body["status"] == "success"
    assert body["tools_used"] == ["rag_search"]


@pytest.mark.parametrize("framework", ["core", "langgraph", "llamaindex"])
def test_query_each_framework_document_question(client, framework):
    r = client.post("/query", json={"query": "When is the project deadline?", "framework": framework})
    assert r.status_code == 200
    body = r.json()
    assert body["framework"] == framework
    assert body["status"] == "success"
    assert body["tools_used"] == ["rag_search"]
    ev = body["evidence"][0]
    assert ev["source"] == "rules.pdf"
    assert ev["page"] == 4
    assert ev["chunk_id"] == "rules.pdf:4:0"
    assert ev["text"]


@pytest.mark.parametrize("framework", ["core", "langgraph", "llamaindex"])
def test_query_calculator(client, framework):
    r = client.post("/query", json={"query": "What is 347 * 29?", "framework": framework})
    assert r.status_code == 200
    body = r.json()
    assert body["tools_used"] == ["calculator"]
    assert body["answer"] == "10063"
    assert body["evidence"] == []


def test_invalid_framework(client):
    r = client.post("/query", json={"query": "hi", "framework": "tensorflow"})
    assert r.status_code == 400
    assert "unsupported framework" in r.json()["detail"]


def test_empty_query_rejected(client):
    r = client.post("/query", json={"query": ""})
    assert r.status_code == 422  # pydantic min_length validation


def test_whitespace_query_rejected(client):
    r = client.post("/query", json={"query": "   "})
    assert r.status_code == 400


def test_response_has_contract_shape(client):
    r = client.post("/query", json={"query": "When is the project deadline?"})
    body = r.json()
    assert set(["answer", "status", "evidence", "tool_calls", "tools_used", "framework"]).issubset(body)


def test_query_is_persisted(client, db_path):
    from database import db

    client.post("/query", json={"query": "When is the project deadline?", "framework": "langgraph"})
    runs = db.list_runs(db_path)
    assert len(runs) == 1
    assert runs[0]["query"] == "When is the project deadline?"
    assert runs[0]["framework"] == "langgraph"
    assert runs[0]["status"] == "success"
    assert runs[0]["tools_used"] == "rag_search"


def test_persistence_does_not_change_response_shape(client):
    r = client.post("/query", json={"query": "What is 347 * 29?"})
    body = r.json()
    # exactly the contract fields plus framework; no db fields leak in
    assert set(body) == {"answer", "status", "evidence", "tool_calls", "tools_used", "error", "framework"}


def test_db_failure_does_not_break_query_or_leak(client, monkeypatch):
    from database import db as db_module

    def boom(*args, **kwargs):
        raise sqlite3.OperationalError("no such table: query_runs at /secret/path")

    monkeypatch.setattr(db_module, "record_run", boom)
    r = client.post("/query", json={"query": "What is 347 * 29?"})
    # agent response still returned, no internal details leaked
    assert r.status_code == 200
    body = r.json()
    assert body["answer"] == "10063"
    assert "secret" not in r.text and "query_runs" not in r.text
