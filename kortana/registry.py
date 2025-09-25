"""Registry for discovery of capabilities, tools, and external resources."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class CapabilityRegistry:
    """Thread-safe registry for capability handler discovery."""

    def __init__(self) -> None:
        self._handlers: dict[str, Callable[[dict[str, Any]], Any]] = {}

    def register(self, name: str, handler: Callable[[dict[str, Any]], Any]) -> None:
        if name in self._handlers:
            raise ValueError(f"Capability '{name}' already registered.")
        self._handlers[name] = handler

    def get(self, name: str) -> Callable[[dict[str, Any]], Any]:
        try:
            return self._handlers[name]
        except KeyError as exc:
            raise KeyError(f"Capability '{name}' has not been registered.") from exc

    def hydrate_agent(self, agent_profile) -> None:
        """Attach registered handlers to capabilities where available."""

        for capability in agent_profile.capabilities:
            if capability.handler is None and capability.name in self._handlers:
                capability.handler = self._handlers[capability.name]

    def list(self) -> dict[str, Callable[[dict[str, Any]], Any]]:
        return dict(self._handlers)
