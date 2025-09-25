"""Task graph and lifecycle management utilities."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import networkx as nx


class TaskStatus(str, Enum):
    """Lifecycle phases for tasks executed by the orchestrator."""

    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    FAILED = "failed"
    COMPLETED = "completed"


@dataclass(slots=True)
class Task:
    """Represents a unit of work that can be executed by an agent."""

    identifier: str
    summary: str
    handler: Callable[[dict[str, Any]], Any]
    payload: dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    requires: set[str] = field(default_factory=set)
    produced: Any | None = None
    error: str | None = None

    def mark_ready(self) -> None:
        self.status = TaskStatus.READY

    def mark_running(self) -> None:
        self.status = TaskStatus.RUNNING

    def mark_completed(self, output: Any) -> None:
        self.status = TaskStatus.COMPLETED
        self.produced = output

    def mark_failed(self, message: str) -> None:
        self.status = TaskStatus.FAILED
        self.error = message


class TaskGraph:
    """DAG wrapper around NetworkX to model task dependencies."""

    def __init__(self) -> None:
        self._graph: nx.DiGraph = nx.DiGraph()

    def add_task(self, task: Task) -> None:
        if task.identifier in self._graph:
            raise ValueError(f"Task '{task.identifier}' already exists in the graph.")
        self._graph.add_node(task.identifier, task=task)

    def add_dependency(self, source: str, target: str) -> None:
        if source == target:
            raise ValueError("A task cannot depend on itself.")
        self._graph.add_edge(source, target)
        if not nx.is_directed_acyclic_graph(self._graph):
            self._graph.remove_edge(source, target)
            raise ValueError("Dependency would create a cycle in the task graph.")
        task = self._graph.nodes[target]["task"]
        task.requires.add(source)

    def tasks(self) -> Iterable[Task]:
        return (self._graph.nodes[node]["task"] for node in self._graph.nodes)

    def ready_tasks(self) -> Iterable[Task]:
        for node in nx.topological_sort(self._graph):
            task: Task = self._graph.nodes[node]["task"]
            if task.status in {TaskStatus.PENDING, TaskStatus.BLOCKED}:
                if all(
                    self._graph.nodes[dep]["task"].status == TaskStatus.COMPLETED
                    for dep in task.requires
                ):
                    task.mark_ready()
                    yield task
                else:
                    task.status = TaskStatus.BLOCKED

    def mark_dependency_completed(self, identifier: str) -> None:
        for _, target in self._graph.out_edges(identifier):
            task: Task = self._graph.nodes[target]["task"]
            if identifier in task.requires:
                task.requires.remove(identifier)

    def __len__(self) -> int:
        return len(self._graph.nodes)


class TaskQueue:
    """FIFO queue that surfaces ready tasks while respecting dependencies."""

    def __init__(self, graph: TaskGraph):
        self.graph = graph
        self._queue: deque[str] = deque()

    def refill(self) -> None:
        for task in self.graph.ready_tasks():
            if task.identifier not in self._queue:
                self._queue.append(task.identifier)

    def pop(self) -> Task | None:
        while self._queue:
            identifier = self._queue.popleft()
            task = next(
                (t for t in self.graph.tasks() if t.identifier == identifier),
                None,
            )
            if task is None:
                continue
            if task.status is TaskStatus.READY:
                task.mark_running()
                return task
        return None

    def __len__(self) -> int:
        return len(self._queue)

    def __bool__(self) -> bool:
        return bool(self._queue)
