import pytest

from kortana.tasks import Task, TaskGraph, TaskQueue


def noop_handler(payload):
    return payload


def test_task_graph_detects_cycles():
    graph = TaskGraph()
    graph.add_task(Task("a", "A", noop_handler))
    graph.add_task(Task("b", "B", noop_handler))
    graph.add_dependency("a", "b")
    with pytest.raises(ValueError):
        graph.add_dependency("b", "a")


def test_task_queue_refill_and_pop():
    graph = TaskGraph()
    t1 = Task("a", "Milestone: A", noop_handler)
    t2 = Task("b", "Milestone: B", noop_handler)
    graph.add_task(t1)
    graph.add_task(t2)
    graph.add_dependency("a", "b")

    queue = TaskQueue(graph)
    queue.refill()

    task = queue.pop()
    assert task is not None
    assert task.identifier == "a"
    task.mark_completed(None)
    graph.mark_dependency_completed(task.identifier)

    queue.refill()
    task = queue.pop()
    assert task is not None
    assert task.identifier == "b"

    assert queue.pop() is None
