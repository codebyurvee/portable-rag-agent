import pytest

from app.frameworks.llamaindex.agent import LlamaIndexAgent
from app.agent.contract import Agent
from app.agent.schemas import AgentRequest, AgentResponse, AgentStatus


class FakeRetriever:
    def __init__(self, hits):
        self._hits = hits

    def retrieve(self, query, top_k=4):
        return self._hits[:top_k]


DOC_HITS = [
    {"source": "rules.pdf", "page": 4, "chunk_id": "rules.pdf:4:0",
     "text": "The project deadline is October 3 2026."},
]


def make_agent(hits):
    return LlamaIndexAgent(retriever=FakeRetriever(hits))


def test_implements_agent_contract():
    agent = make_agent(DOC_HITS)
    assert isinstance(agent, Agent)
    assert isinstance(agent.run(AgentRequest(query="hello")), AgentResponse)


def test_passport_identifies_llamaindex():
    p = make_agent(DOC_HITS).passport()
    assert p.framework == "llamaindex"
    assert p.name == "portable-rag-agent"
    assert "rag_search" in p.tools and "calculator" in p.tools


def test_document_question_uses_rag_and_preserves_evidence():
    resp = make_agent(DOC_HITS).run(AgentRequest(query="When is the project deadline?"))
    assert resp.status is AgentStatus.SUCCESS
    assert resp.tools_used == ["rag_search"]
    ev = resp.evidence[0]
    assert ev.source == "rules.pdf"
    assert ev.page == 4
    assert ev.chunk_id == "rules.pdf:4:0"


def test_arithmetic_question_uses_calculator():
    resp = make_agent(DOC_HITS).run(AgentRequest(query="What is 347 * 29?"))
    assert resp.tools_used == ["calculator"]
    assert resp.answer == str(347 * 29)
    assert resp.evidence == []


def test_web_intent_safe_when_disabled():
    resp = make_agent(DOC_HITS).run(AgentRequest(query="latest news about the deadline"))
    assert resp.tools_used == ["rag_search"]
    assert resp.status is AgentStatus.SUCCESS


def test_no_result_is_handled_safely():
    resp = make_agent([]).run(AgentRequest(query="What does the document say about Mars?"))
    assert resp.status is AgentStatus.NO_ANSWER
    assert resp.tools_used == ["rag_search"]
    assert resp.evidence == []
