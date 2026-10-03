import pytest

from app.agent.core import AgentCore, decide_tool
from app.agent.model import QwenModel
from app.agent.schemas import AgentRequest, AgentResponse, AgentStatus


class FakeRetriever:
    def __init__(self, hits):
        self._hits = hits

    def retrieve(self, query, top_k=4):
        return self._hits[:top_k]


def make_agent(hits):
    return AgentCore(retriever=FakeRetriever(hits))


DOC_HITS = [
    {"source": "rules.pdf", "page": 4, "chunk_id": "rules.pdf:4:0",
     "text": "The project deadline is October 3 2026."},
]


def test_decide_tool_routing():
    assert decide_tool("What is 347 * 29?", web_enabled=False) == "calculator"
    assert decide_tool("When is the deadline?", web_enabled=False) == "rag_search"
    assert decide_tool("latest news on AI", web_enabled=True) == "web_search"
    # web routing only when web is enabled
    assert decide_tool("latest news on AI", web_enabled=False) == "rag_search"


def test_arithmetic_question_uses_calculator():
    agent = make_agent(DOC_HITS)
    resp = agent.run(AgentRequest(query="What is 347 * 29?"))
    assert isinstance(resp, AgentResponse)
    assert resp.status is AgentStatus.SUCCESS
    assert resp.answer == str(347 * 29)
    assert resp.tools_used == ["calculator"]
    assert resp.evidence == []


def test_document_question_uses_rag_with_evidence():
    agent = make_agent(DOC_HITS)
    resp = agent.run(AgentRequest(query="When is the project deadline?"))
    assert resp.status is AgentStatus.SUCCESS
    assert resp.tools_used == ["rag_search"]
    assert resp.evidence
    ev = resp.evidence[0]
    assert ev.source == "rules.pdf"
    assert ev.page == 4
    # offline fallback returns the retrieved passage; evidence is preserved
    assert "October 3 2026" in resp.answer


def test_no_result_is_handled_safely():
    agent = make_agent([])
    resp = agent.run(AgentRequest(query="What does the document say about Mars?"))
    assert resp.status is AgentStatus.NO_ANSWER
    assert resp.tools_used == ["rag_search"]
    assert resp.evidence == []


def test_response_serializes_to_contract_shape():
    agent = make_agent(DOC_HITS)
    data = agent.run(AgentRequest(query="When is the project deadline?")).to_dict()
    assert set(["answer", "status", "evidence", "tool_calls", "tools_used"]).issubset(data)
    assert data["status"] == "success"
    assert data["tools_used"] == ["rag_search"]
    assert data["evidence"][0]["source"] == "rules.pdf"


def test_passport_reports_tools():
    agent = make_agent(DOC_HITS)
    p = agent.passport()
    assert p.name == "portable-rag-agent"
    assert "rag_search" in p.tools and "calculator" in p.tools


def test_qwen_adapter_requires_configuration():
    model = QwenModel(api_key=None, base_url=None)
    assert model.configured is False
    with pytest.raises(RuntimeError):
        model.generate([{"role": "user", "content": "hi"}])


def test_qwen_adapter_reports_configured_with_env(monkeypatch):
    model = QwenModel(api_key="k", base_url="https://example.test/v1", model="qwen/qwen3-8b")
    assert model.configured is True
    assert model.model == "qwen/qwen3-8b"
