"""LangGraph agent: orchestrates the shared AgentCore steps as a small graph.

The tool implementations, decision logic, evidence handling and Qwen call all
live in app.agent.core; this module only wires them into a LangGraph flow so the
external Agent contract stays identical to AgentCore.
"""

from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from app.agent.contract import Agent
from app.agent.core import AgentCore, decide_tool
from app.agent.schemas import AgentRequest, AgentResponse
from app.agent.passport import AgentPassport


class _State(TypedDict):
    query: str
    tool: str
    response: AgentResponse


class LangGraphAgent(Agent):
    name = "portable-rag-agent"

    def __init__(self, retriever, model=None):
        self.core = AgentCore(retriever=retriever, model=model, framework="langgraph")
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(_State)
        graph.add_node("decide", self._decide)
        graph.add_node("calculator", self._calculator)
        graph.add_node("rag_search", self._rag)
        graph.add_node("web_search", self._web)

        graph.add_edge(START, "decide")
        graph.add_conditional_edges(
            "decide",
            lambda state: state["tool"],
            {"calculator": "calculator", "rag_search": "rag_search", "web_search": "web_search"},
        )
        for node in ("calculator", "rag_search", "web_search"):
            graph.add_edge(node, END)
        return graph.compile()

    def _decide(self, state: _State) -> _State:
        return {"tool": decide_tool(state["query"], self.core.web.enabled)}

    def _calculator(self, state: _State) -> _State:
        return {"response": self.core._run_calculator(state["query"])}

    def _rag(self, state: _State) -> _State:
        return {"response": self.core._run_rag(state["query"])}

    def _web(self, state: _State) -> _State:
        return {"response": self.core._run_web(state["query"])}

    def passport(self) -> AgentPassport:
        p = self.core.passport()
        p.framework = "langgraph"
        return p

    def run(self, request: AgentRequest) -> AgentResponse:
        final = self.graph.invoke({"query": request.query.strip()})
        return final["response"]
