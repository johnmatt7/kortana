from kortana.agents import AgentProfile, AgentRuntime, Capability
from kortana.orchestrator import Orchestrator


def make_agent() -> AgentRuntime:
    profile = AgentProfile(
        identifier="builder",
        name="Builder",
        description="Executes build tasks",
        capabilities=[
            Capability(
                name="echo",
                description="Echo back payload",
            )
        ],
    )

    def handler(payload: dict[str, str]) -> str:
        return payload.get("message", "")

    profile.capabilities[0].handler = handler
    return AgentRuntime(profile=profile)


def test_orchestrator_runs_tasks_in_order():
    agent = make_agent()
    orchestrator = Orchestrator()
    orchestrator.register_agent(agent)

    orchestrator.submit_task(
        identifier="t1",
        summary="Milestone: echo message 1",
        capability="echo",
        payload={"message": "hello"},
    )
    orchestrator.submit_task(
        identifier="t2",
        summary="Milestone: echo message 2",
        capability="echo",
        payload={"message": "world"},
        depends_on=["t1"],
    )

    results = orchestrator.run()
    assert [result.output for result in results] == ["hello", "world"]
    assert len(list(orchestrator.event_bus.history("task.completed"))) == 2
