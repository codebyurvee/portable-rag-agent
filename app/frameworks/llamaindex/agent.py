"""LlamaIndex agent: a small Workflow that orchestrates the shared AgentCore steps.

Tool implementations, decision logic, evidence handling and the Qwen call all
live in app.agent.core; this module only wires them into a LlamaIndex Workflow so
the external Agent contract stays identical to AgentCore and LangGraphAgent.
"""

import asyncio

from llama_index.core.workflow import Workflow, StartEvent, StopEvent, step, Event

from app.agent.contract import Agent
from app.agent.core import AgentCore, decide_tool
from app.agent.schemas import AgentRequest, AgentResponse
from app.agent.passport import AgentPassport


class ToolEvent(Event):
    query: str
    tool: str


class _AgentWorkflow(Workflow):
    def __init__(self, core: AgentCore, **kwargs):
        super().__init__(**kwargs)
        self.core = core

    @step
    async def decide(self, ev: StartEvent) -> ToolEvent:
        query = ev.query.strip()
        return ToolEvent(query=query, tool=decide_tool(query, self.core.web.enabled))

    @step
    async def act(self, ev: ToolEvent) -> StopEvent:
        if ev.tool == "calculator":
            response = self.core._run_calculator(ev.query)
        elif ev.tool == "web_search":
            response = self.core._run_web(ev.query)
        else:
            response = self.core._run_rag(ev.query)
        return StopEvent(result=response)


class LlamaIndexAgent(Agent):
    name = "portable-rag-agent"

    def __init__(self, retriever, model=None):
        self.core = AgentCore(retriever=retriever, model=model, framework="llamaindex")
        self.workflow = _AgentWorkflow(self.core, timeout=60)

    def passport(self) -> AgentPassport:
        p = self.core.passport()
        p.framework = "llamaindex"
        return p

    async def _arun(self, query: str) -> AgentResponse:
        return await self.workflow.run(query=query)

    def run(self, request: AgentRequest) -> AgentResponse:
        return asyncio.run(self._arun(request.query.strip()))
