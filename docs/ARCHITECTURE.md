# Kortana Architecture Overview

## Core packages

| Module | Purpose |
| --- | --- |
| `kortana.agents` | Declarative agent profiles and runtime memory/state helpers. |
| `kortana.tasks` | Dependency-aware task graph primitives and execution queue. |
| `kortana.orchestrator` | Coordinates agents, executes capability handlers, and captures results. |
| `kortana.events` | Structured event bus for telemetry, spans, and audit trails. |
| `kortana.storage` | Persistence interfaces for orchestrator state and memory snapshots. |
| `kortana.planning` | Generates milestone groupings and critical paths for proactive planning. |
| `kortana.registry` | Dynamically binds capability handlers to agent profiles. |
| `kortana.cli` | Typer-powered command-line experience for demos and tooling. |

## Execution flow

1. **Register agents** – Agents are constructed from JSON or code and registered with the
   orchestrator.
2. **Submit tasks** – Each task references a capability and optional dependencies. Tasks compile into
   a DAG maintained by `TaskGraph`.
3. **Run orchestration** – The orchestrator drains the `TaskQueue`, executes capability handlers,
   publishes events, and records results.
4. **Reflect and plan** – Agents update their memory from event spans; planners compute milestones and
   critical paths to inform next actions.

## Extension points

- **Capability handlers** – Implement Python callables or wrappers to external APIs and register them
  via `CapabilityRegistry`.
- **Event sinks** – Subscribe to the event bus to forward telemetry to observability stacks or chat
  systems.
- **State backends** – Implement the `StateBackend` protocol to persist orchestrations into databases,
  blob stores, or version control.
- **CLI commands** – Extend `kortana.cli` with new commands for automation pipelines or workflow
  templates.
