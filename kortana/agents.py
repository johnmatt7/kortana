"""Agent definitions and runtime state management for Kortana."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, ValidationError


class Capability(BaseModel):
    """Describes an action the agent can execute autonomously."""

    name: str = Field(..., description="Human readable identifier for the capability.")
    description: str = Field(..., description="Summary of what the capability does.")
    inputs: dict[str, str] = Field(default_factory=dict, description="Input schema hints.")
    outputs: dict[str, str] = Field(default_factory=dict, description="Output schema hints.")
    handler: Callable[[dict[str, Any]], Any] | None = Field(
        default=None, description="Optional python callable used for execution."
    )

    model_config = {
        "arbitrary_types_allowed": True,
    }


class AgentStatus(str, Enum):
    """Possible runtime states for an agent."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"


class AgentProfile(BaseModel):
    """Declarative configuration for an autonomous agent persona."""

    identifier: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$", description="Unique agent id.")
    name: str = Field(..., description="Display name for the agent.")
    description: str = Field(..., description="High level purpose for the agent.")
    goals: list[str] = Field(default_factory=list, description="Objectives that guide planning.")
    capabilities: list[Capability] = Field(
        default_factory=list, description="Catalog of actions available to the agent."
    )
    context_window: int = Field(
        default=20,
        ge=1,
        description="Number of past events the agent should remember for planning.",
    )

    def add_capability(self, capability: Capability) -> None:
        """Attach a new capability to the agent profile."""

        if capability.name in {c.name for c in self.capabilities}:
            raise ValueError(f"Capability '{capability.name}' already exists on {self.identifier}.")
        self.capabilities.append(capability)


class AgentRuntime(BaseModel):
    """Mutable runtime data for an autonomous agent instance."""

    profile: AgentProfile
    status: AgentStatus = AgentStatus.IDLE
    active_task: str | None = None
    memory: list[str] = Field(default_factory=list, description="Rolling event log for reflection.")

    model_config = {
        "validate_assignment": True,
        "arbitrary_types_allowed": True,
    }

    def update_status(self, status: AgentStatus) -> None:
        """Safely transition the agent into a new status."""

        if self.status == AgentStatus.STOPPED and status != AgentStatus.STOPPED:
            raise RuntimeError("Stopped agents cannot transition back to another state.")
        self.status = status

    def remember(self, message: str) -> None:
        """Persist a message into the agent's rolling memory buffer."""

        self.memory.append(message)
        overflow = len(self.memory) - self.profile.context_window
        if overflow > 0:
            del self.memory[0:overflow]

    def validate_capability(self, capability_name: str) -> Capability:
        """Ensure the capability exists and return it."""

        for capability in self.profile.capabilities:
            if capability.name == capability_name:
                return capability
        raise KeyError(f"Capability '{capability_name}' is not registered on agent {self.profile.name}.")

    def execute(self, capability_name: str, payload: dict[str, Any]) -> Any:
        """Execute the handler for a capability with structured payload validation."""

        capability = self.validate_capability(capability_name)
        handler = capability.handler
        if handler is None:
            raise RuntimeError(f"Capability '{capability_name}' does not have an execution handler.")

        self.update_status(AgentStatus.RUNNING)
        try:
            return handler(payload)
        finally:
            self.update_status(AgentStatus.IDLE)


def build_agent(profile_data: dict[str, Any]) -> AgentRuntime:
    """Construct an :class:`AgentRuntime` from loosely structured profile data."""

    try:
        profile = AgentProfile.model_validate(profile_data)
    except ValidationError as exc:  # pragma: no cover - validation details for humans
        raise ValueError(f"Invalid agent profile: {exc}") from exc
    return AgentRuntime(profile=profile)


def iter_capabilities(agent: AgentRuntime) -> Iterable[str]:
    """Yield capability names for convenience in CLI/UX layers."""

    return (capability.name for capability in agent.profile.capabilities)
