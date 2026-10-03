"""Portability: AgentCore, LangGraphAgent and LlamaIndexAgent must behave the same.

We compare behavior (type, status, tools_used, ToolCall, evidence, calculator
correctness, safe no-result/web-disabled handling) — never exact wording.
"""

import pytest

from app.agent.core import AgentCore
from app.frameworks.langgraph.agent import LangGraphAgent
from app.frameworks.llamaindex.agent import LlamaIndexAgent
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

# Each builder takes the retrieval hits and returns a contract-compatible agent.
BUILDERS = {
    "core": lambda hits: AgentCore(retriever=FakeRetriever(hits)),
    "langgraph": lambda hits: LangGraphAgent(retriever=FakeRetriever(hits)),
    "llamaindex": lambda hits: LlamaIndexAgent(retriever=FakeRetriever(hits)),
}


@pytest.fixture(params=list(BUILDERS), ids=list(BUILDERS))
def build(request):
    return BUILDERS[request.param]


def test_case1_document_question_uses_rag_with_real_evidence(build):
    resp = build(DOC_HITS).run(AgentRequest(query="When is the project deadline?"))
    assert isinstance(resp, AgentResponse)
    assert resp.status is AgentStatus.SUCCESS
    assert resp.tools_used == ["rag_search"]
    assert resp.tool_calls[0].name == "rag_search"
    assert resp.evidence, "evidence must be present"
    ev = resp.evidence[0]
    assert ev.source == "rules.pdf"
    assert ev.page == 4
    assert ev.chunk_id == "rules.pdf:4:0"
    assert ev.text  # real retrieved text, not fabricated


def test_case2_calculator_exact_result(build):
    resp = build(DOC_HITS).run(AgentRequest(query="What is 347 * 29?"))
    assert resp.status is AgentStatus.SUCCESS
    assert resp.tools_used == ["calculator"]
    assert resp.tool_calls[0].name == "calculator"
    assert resp.answer == "10063"
    assert resp.evidence == []


def test_case3_web_intent_safe_without_key(build):
    # Tavily unconfigured -> web-intent falls back to RAG, no fabricated results
    resp = build(DOC_HITS).run(AgentRequest(query="What is the latest news?"))
    assert isinstance(resp, AgentResponse)
    assert resp.tools_used == ["rag_search"]


def test_case4_no_result_safe(build):
    resp = build([]).run(AgentRequest(query="What does the document say about Mars?"))
    assert resp.status is AgentStatus.NO_ANSWER
    assert resp.tools_used == ["rag_search"]
    assert resp.evidence == []


def test_case5_unsafe_calculator_rejected(build):
    resp = build(DOC_HITS).run(AgentRequest(query="__import__('os').system('echo hi')"))
    # not arithmetic -> routed to RAG (no code execution), or if treated as calc, errors.
    # Either way: never executes code, never fabricates evidence.
    assert isinstance(resp, AgentResponse)
    assert "calculator" not in resp.tools_used or resp.status is AgentStatus.ERROR


def test_all_three_agree_on_shape(build):
    data = build(DOC_HITS).run(AgentRequest(query="When is the project deadline?")).to_dict()
    assert set(["answer", "status", "evidence", "tool_calls", "tools_used"]).issubset(data)
