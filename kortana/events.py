"""Lightweight event bus for observability and agent coordination."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Generator, Iterable
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class Event:
    """Represents a discrete event emitted by the orchestrator or agents."""

    topic: str
    payload: dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EventBus:
    """Publish/subscribe broker used for tracing agent activity."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[Event], None]]] = defaultdict(list)
        self._history: list[Event] = []

    def subscribe(self, topic: str, listener: Callable[[Event], None]) -> None:
        self._subscribers[topic].append(listener)

    def emit(self, topic: str, payload: dict[str, Any] | None = None) -> Event:
        event = Event(topic=topic, payload=payload or {})
        self._history.append(event)
        for listener in self._subscribers.get(topic, []):
            listener(event)
        for listener in self._subscribers.get("*", []):
            listener(event)
        return event

    def history(self, topic: str | None = None) -> Iterable[Event]:
        if topic is None:
            yield from self._history
        else:
            yield from (event for event in self._history if event.topic == topic)

    @contextmanager
    def span(self, topic: str, payload: dict[str, Any] | None = None) -> Generator[Event, None, None]:
        start = self.emit(f"{topic}.start", payload)
        try:
            yield start
        finally:
            end_payload = dict(payload or {})
            end_payload["started_at"] = start.created_at.isoformat()
            self.emit(f"{topic}.end", end_payload)
