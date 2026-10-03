import pytest

from app.agent.schemas import Evidence
from app.tools.calculator import CalculatorTool, calculate
from app.tools.rag_search import RagSearchTool
from app.tools.web_search import WebSearchTool


class FakeRetriever:
    def __init__(self, hits):
        self._hits = hits

    def retrieve(self, query, top_k=4):
        return self._hits[:top_k]


def test_calculator_correct_result():
    tool = CalculatorTool()
    assert tool.run("347 * 29") == {"result": 347 * 29, "status": "success"}
    assert calculate("2 + 3 * 4") == 14
    assert calculate("(1 + 2) ** 3") == 27


def test_calculator_rejects_unsafe_expressions():
    tool = CalculatorTool()
    for expr in ["__import__('os').system('echo hi')", "open('x')", "a + 1", "1;2", "print(1)"]:
        out = tool.run(expr)
        assert out["status"] == "error"
        assert out["result"] is None


def test_rag_tool_returns_real_evidence():
    hits = [
        {"source": "doc.pdf", "page": 2, "chunk_id": "doc.pdf:2:0", "text": "the answer is 42"},
    ]
    tool = RagSearchTool(FakeRetriever(hits))
    out = tool.run("what is the answer")
    assert out["status"] == "success"
    ev = out["evidence"][0]
    assert isinstance(ev, Evidence)
    assert ev.source == "doc.pdf"
    assert ev.page == 2
    assert ev.chunk_id == "doc.pdf:2:0"
    assert ev.text == "the answer is 42"


def test_rag_tool_no_result_status():
    tool = RagSearchTool(FakeRetriever([]))
    out = tool.run("nothing here")
    assert out["status"] == "no_answer"
    assert out["evidence"] == []


def test_web_search_disabled_without_key():
    tool = WebSearchTool(api_key=None)
    assert tool.enabled is False
    out = tool.run("latest news")
    assert out["status"] == "no_answer"
    assert out["results"] == []


def test_web_search_enabled_with_key():
    tool = WebSearchTool(api_key="real-key")
    assert tool.enabled is True
    assert tool.api_key == "real-key"


def test_web_search_blank_key_is_disabled():
    # empty or whitespace-only keys must not count as configured
    assert WebSearchTool(api_key="").enabled is False
    assert WebSearchTool(api_key="   ").enabled is False


def test_web_search_strips_surrounding_whitespace():
    tool = WebSearchTool(api_key="  real-key  ")
    assert tool.enabled is True
    assert tool.api_key == "real-key"


def test_web_search_reads_env_var(monkeypatch):
    monkeypatch.setenv("WEB_SEARCH_API_KEY", "env-key")
    assert WebSearchTool().enabled is True
    monkeypatch.setenv("WEB_SEARCH_API_KEY", "  ")
    assert WebSearchTool().enabled is False
