# Kortana

Kortana is an autonomy-first orchestration toolkit built for AI agents that collaborate on
software engineering and cloud operations. The project focuses on three pillars:

1. **Strategic autonomy** – agents reason over roadmaps, dependencies, and delivery risk.
2. **Deep tool integration** – capability handlers can call internal Python functions or external
   services to execute coding, testing, and deployment workflows.
3. **Cloud-native delivery** – orchestration primitives embrace infrastructure-as-code,
   reproducible environments, and asynchronous collaboration between specialized agents.

## Getting started

```bash
pip install -e .[dev]
```

The CLI ships with a `demo` workflow that provisions a strategic planning agent and executes a
simple task graph:

```bash
kortana demo
```

To generate a starter JSON profile for your own agent persona:

```bash
kortana profile --template > architect.json
```

Edit the resulting file to match your environment and invoke the demo with a custom profile:

```bash
kortana demo --config architect.json
```

## Concepts

### Agents

Agents are defined with a declarative profile capturing their goals, memory window, and executable
capabilities. A capability is a semantic contract between the orchestrator and some callable
function. The callable can be implemented in Python, proxied to an API, or act as a bridge to
another autonomous system.

### Orchestrator

The `Orchestrator` coordinates multi-agent workflows. It maintains a task dependency graph,
schedules ready tasks, executes capability handlers, and emits structured events via an in-process
bus. Observability is built-in; hook the bus to stream events into metrics, tracing, or chat.

### Planning

`RoadmapPlanner` provides insight on milestones and critical paths derived from the task graph.
This enables higher-level agents to reason about bottlenecks and reprioritize work dynamically.

### State and persistence

State backends allow persisting orchestrator snapshots either in-memory (for tests) or to disk via
JSON. Extend `StateBackend` to integrate with databases or cloud object storage.

## Roadmap

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for a staged plan targeting maximum agent autonomy in
software/cloud development. Contributions are welcome through issues and pull requests.
