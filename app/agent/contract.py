"""The Agent Contract: the framework-independent boundary both frameworks implement."""

from abc import ABC, abstractmethod

from app.agent.schemas import (
    AgentRequest,
    AgentResponse,
    AgentStatus,
    Evidence,
    ToolCall,
)
from app.agent.passport import AgentPassport

__all__ = [
    "Agent",
    "AgentRequest",
    "AgentResponse",
    "AgentStatus",
    "Evidence",
    "ToolCall",
    "AgentPassport",
]


class Agent(ABC):
    @abstractmethod
    def run(self, request: AgentRequest) -> AgentResponse:
        ...

    @abstractmethod
    def passport(self) -> AgentPassport:
        ...
