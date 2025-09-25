"""Utility routines for generating execution plans and work breakdowns."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import networkx as nx

from .tasks import Task, TaskGraph


@dataclass(slots=True)
class Milestone:
    """Represents a high level deliverable with associated tasks."""

    name: str
    description: str
    tasks: list[str]


class RoadmapPlanner:
    """Generates milestone-based plans for orchestrator consumption."""

    def __init__(self, graph: TaskGraph) -> None:
        self.graph = graph

    def milestones(self) -> Iterable[Milestone]:
        buckets: dict[str, Milestone] = {}
        for task in self.graph.tasks():
            milestone = task.summary.split(":", 1)[0]
            buckets.setdefault(
                milestone,
                Milestone(name=milestone, description=f"Milestone for {milestone}", tasks=[]),
            ).tasks.append(task.identifier)
        yield from buckets.values()

    def critical_path(self) -> list[Task]:
        graph = self.graph._graph  # type: ignore[attr-defined]
        if not graph.nodes:
            return []
        if not nx.is_directed_acyclic_graph(graph):
            raise RuntimeError("Task graph must be a DAG to compute critical path.")
        path = nx.dag_longest_path(graph)
        return [graph.nodes[node]["task"] for node in path]
