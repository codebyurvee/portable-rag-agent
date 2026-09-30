"""Framework-independent data types shared by both agent implementations."""

from dataclasses import dataclass, field, asdict
from enum import Enum


class AgentStatus(str, Enum):
    SUCCESS = "success"
    NO_ANSWER = "no_answer"
    ERROR = "error"


@dataclass
class Evidence:
    source: str
    text: str
    page: int | None = None
    chunk_id: str | None = None

    def __post_init__(self):
        if not self.source:
            raise ValueError("Evidence.source is required")
        if not self.text:
            raise ValueError("Evidence.text is required")


@dataclass
class ToolCall:
    name: str
    args: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.name:
            raise ValueError("ToolCall.name is required")


@dataclass
class AgentRequest:
    query: str
    framework: str | None = None

    def __post_init__(self):
        if not self.query or not self.query.strip():
            raise ValueError("AgentRequest.query is required")


@dataclass
class AgentResponse:
    answer: str
    status: AgentStatus = AgentStatus.SUCCESS
    evidence: list[Evidence] = field(default_factory=list)
    tool_calls: list[ToolCall] = field(default_factory=list)
    error: str | None = None

    @property
    def tools_used(self) -> list[str]:
        return [t.name for t in self.tool_calls]

    def to_dict(self) -> dict:
        data = asdict(self)
        data["status"] = self.status.value
        data["tools_used"] = self.tools_used
        return data
