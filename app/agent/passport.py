"""Agent Passport: minimal metadata describing an agent implementation."""

from dataclasses import dataclass, field, asdict


@dataclass
class AgentPassport:
    name: str
    framework: str
    tools: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.name:
            raise ValueError("AgentPassport.name is required")
        if not self.framework:
            raise ValueError("AgentPassport.framework is required")

    def to_dict(self) -> dict:
        return asdict(self)
