"""Autonomous workflow orchestrator for Kortana agents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .agents import AgentRuntime
from .events import EventBus
from .tasks import Task, TaskGraph, TaskQueue


@dataclass(slots=True)
class TaskResult:
    """Captured result emitted after executing a task."""

    identifier: str
    output: Any
    summary: str
    agent_id: str
    capability: str


class Orchestrator:
    """Coordinates agents, tasks, and observability for autonomous execution."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self.event_bus = event_bus or EventBus()
        self.graph = TaskGraph()
        self.queue = TaskQueue(self.graph)
        self.agents: dict[str, AgentRuntime] = {}
        self._task_agent_map: dict[str, str] = {}
        self._task_capability: dict[str, str] = {}
        self._results: list[TaskResult] = []

    # ------------------------------------------------------------------
    # Agent registration & discovery
    # ------------------------------------------------------------------
    def register_agent(self, agent: AgentRuntime) -> None:
        identifier = agent.profile.identifier
        if identifier in self.agents:
            raise ValueError(f"Agent '{identifier}' is already registered.")
        self.agents[identifier] = agent
        self.event_bus.emit(
            "agent.registered",
            {
                "agent_id": identifier,
                "name": agent.profile.name,
                "capabilities": list(agent.profile.capabilities),
            },
        )

    def find_agent_with_capability(self, capability_name: str) -> AgentRuntime:
        for agent in self.agents.values():
            try:
                agent.validate_capability(capability_name)
            except KeyError:
                continue
            return agent
        raise LookupError(f"No registered agent provides capability '{capability_name}'.")

    # ------------------------------------------------------------------
    # Task submission and execution
    # ------------------------------------------------------------------
    def submit_task(
        self,
        identifier: str,
        summary: str,
        capability: str,
        payload: dict[str, Any] | None = None,
        *,
        agent_id: str | None = None,
        depends_on: list[str] | None = None,
    ) -> Task:
        agent = self.agents[agent_id] if agent_id else self.find_agent_with_capability(capability)
        payload = payload or {}

        def handler(task_payload: dict[str, Any]) -> Any:
            with self.event_bus.span(
                "task.execute",
                {
                    "task_id": identifier,
                    "agent_id": agent.profile.identifier,
                    "capability": capability,
                },
            ):
                agent.remember(f"Executing {capability} with payload {task_payload!r}")
                result = agent.execute(capability, task_payload)
                agent.remember(f"Completed {capability} -> {result!r}")
                return result

        task = Task(identifier=identifier, summary=summary, handler=handler, payload=payload)
        self.graph.add_task(task)
        for dependency in depends_on or []:
            self.graph.add_dependency(dependency, identifier)
        self.queue.refill()
        self._task_agent_map[identifier] = agent.profile.identifier
        self._task_capability[identifier] = capability
        self.event_bus.emit(
            "task.submitted",
            {
                "task_id": identifier,
                "summary": summary,
                "capability": capability,
                "agent_id": agent.profile.identifier,
            },
        )
        return task

    def _run_task(self, task: Task) -> None:
        try:
            output = task.handler(task.payload)
        except Exception as exc:  # pragma: no cover - surfaced to humans for debugging
            task.mark_failed(str(exc))
            self.event_bus.emit(
                "task.failed",
                {
                    "task_id": task.identifier,
                    "error": str(exc),
                },
            )
        else:
            task.mark_completed(output)
            result = TaskResult(
                identifier=task.identifier,
                output=output,
                summary=task.summary,
                agent_id=self._task_agent_map[task.identifier],
                capability=self._task_capability[task.identifier],
            )
            self._results.append(result)
            self.graph.mark_dependency_completed(task.identifier)
            self.event_bus.emit(
                "task.completed",
                {
                    "task_id": task.identifier,
                    "agent_id": result.agent_id,
                    "capability": result.capability,
                },
            )

    def run(self) -> list[TaskResult]:
        """Process the task queue until all tasks finish or block."""

        while True:
            self.queue.refill()
            task = self.queue.pop()
            if task is None:
                break
            self._run_task(task)
        return list(self._results)

    # ------------------------------------------------------------------
    # Reporting & Introspection
    # ------------------------------------------------------------------
    def results(self) -> list[TaskResult]:
        return list(self._results)

    def reset(self) -> None:
        self.graph = TaskGraph()
        self.queue = TaskQueue(self.graph)
        self._task_agent_map.clear()
        self._task_capability.clear()
        self._results.clear()
        self.event_bus.emit("orchestrator.reset")
