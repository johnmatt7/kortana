"""State persistence interfaces for Kortana."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol


class StateBackend(Protocol):
    """Interface for durable state stores."""

    def load(self) -> dict[str, Any]:
        ...

    def save(self, data: dict[str, Any]) -> None:
        ...


class MemoryBackend:
    """Ephemeral in-memory state backend."""

    def __init__(self) -> None:
        self._state: dict[str, Any] = {}

    def load(self) -> dict[str, Any]:
        return dict(self._state)

    def save(self, data: dict[str, Any]) -> None:
        self._state = dict(data)


class JsonFileBackend:
    """Simple JSON file persistence for orchestrator snapshots."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text())

    def save(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2, sort_keys=True))
