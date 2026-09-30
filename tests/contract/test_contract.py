import pytest

from app.agent.contract import (
    Agent,
    AgentRequest,
    AgentResponse,
    AgentStatus,
    Evidence,
    ToolCall,
    AgentPassport,
)


def test_valid_agent_request():
    req = AgentRequest(query="What is the deadline?")
    assert req.query == "What is the deadline?"
    assert req.framework is None


def test_agent_request_rejects_empty_query():
    with pytest.raises(ValueError):
        AgentRequest(query="   ")


def test_valid_agent_response():
    resp = AgentResponse(answer="October 3, 2026.")
    assert resp.answer == "October 3, 2026."
    assert resp.status is AgentStatus.SUCCESS
    assert resp.evidence == []
    assert resp.tool_calls == []


def test_evidence_structure():
    ev = Evidence(source="rules.pdf", text="deadline is ...", page=4, chunk_id="c1")
    assert ev.source == "rules.pdf"
    assert ev.page == 4
    assert ev.chunk_id == "c1"


def test_evidence_requires_source_and_text():
    with pytest.raises(ValueError):
        Evidence(source="", text="x")
    with pytest.raises(ValueError):
        Evidence(source="rules.pdf", text="")


def test_tool_call_structure():
    call = ToolCall(name="rag_search", args={"query": "deadline"})
    assert call.name == "rag_search"
    assert call.args == {"query": "deadline"}


def test_tool_call_requires_name():
    with pytest.raises(ValueError):
        ToolCall(name="")


def test_status_handling():
    resp = AgentResponse(answer="", status=AgentStatus.NO_ANSWER)
    assert resp.status is AgentStatus.NO_ANSWER
    assert AgentStatus("error") is AgentStatus.ERROR


def test_response_serialization():
    resp = AgentResponse(
        answer="October 3, 2026.",
        evidence=[Evidence(source="rules.pdf", text="...", page=4)],
        tool_calls=[ToolCall(name="rag_search", args={"query": "deadline"})],
    )
    data = resp.to_dict()
    assert data["answer"] == "October 3, 2026."
    assert data["status"] == "success"
    assert data["tools_used"] == ["rag_search"]
    assert data["evidence"][0]["source"] == "rules.pdf"
    assert data["evidence"][0]["page"] == 4


def test_passport_creation_and_serialization():
    p = AgentPassport(name="research-agent", framework="langgraph", tools=["rag_search"])
    assert p.name == "research-agent"
    assert p.to_dict() == {
        "name": "research-agent",
        "framework": "langgraph",
        "tools": ["rag_search"],
    }


def test_passport_requires_name_and_framework():
    with pytest.raises(ValueError):
        AgentPassport(name="", framework="langgraph")
    with pytest.raises(ValueError):
        AgentPassport(name="x", framework="")


def test_agent_is_abstract():
    with pytest.raises(TypeError):
        Agent()
