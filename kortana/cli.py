"""Command line tooling for running Kortana orchestrations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from .agents import AgentProfile, AgentRuntime, Capability, build_agent
from .orchestrator import Orchestrator

app = typer.Typer(help="Kortana - AI autonomy toolkit for software/cloud development")


def _load_profile(path: Path) -> AgentRuntime:
    data = json.loads(path.read_text())
    profile = AgentProfile.model_validate(data)
    return AgentRuntime(profile=profile)


@app.command()
def demo(
    config: Annotated[Path | None, typer.Option(help="Optional path to agent profile JSON.")] = None
) -> None:
    """Run a demonstration orchestration using a sample agent."""

    orchestrator = Orchestrator()

    if config:
        agent = _load_profile(config)
    else:
        agent = build_agent(
            {
                "identifier": "architect",
                "name": "Systems Architect",
                "description": "Designs software delivery plans for cloud-native projects.",
                "goals": [
                    "Translate high level product requirements into technical execution plans.",
                    "Coordinate specialized agents by delegating tasks based on capabilities.",
                    "Continuously evaluate risks and surface mitigation strategies.",
                ],
                "capabilities": [
                    {
                        "name": "generate_plan",
                        "description": "Create a milestone oriented implementation plan for a project.",
                    },
                    {
                        "name": "risk_register",
                        "description": "Identify delivery risks with mitigation steps.",
                    },
                ],
            }
        )

        def plan_handler(payload: dict[str, str]) -> str:
            requirement = payload.get("requirement", "undefined")
            return (
                f"Plan for {requirement}: 1) Capture requirements 2) Implement 3) Ship with QA"
            )

        def risk_handler(payload: dict[str, str]) -> str:
            context = payload.get("context", "")
            return f"Risks for {context}: schedule slip, cloud cost overrun, API instability"

        agent.profile.capabilities[0].handler = plan_handler
        agent.profile.capabilities[1].handler = risk_handler

    orchestrator.register_agent(agent)

    orchestrator.submit_task(
        identifier="plan",
        summary="Generate execution plan",
        capability="generate_plan",
        payload={"requirement": "Kortana v0 launch"},
    )
    orchestrator.submit_task(
        identifier="risks",
        summary="Create risk register",
        capability="risk_register",
        payload={"context": "Kortana v0 launch"},
        depends_on=["plan"],
    )

    typer.echo("Running orchestration...")
    results = orchestrator.run()
    for result in results:
        typer.echo(f"Task {result.identifier} completed by {result.agent_id}: {result.output}")


@app.command()
def profile(
    template: Annotated[bool, typer.Option(help="Emit a template agent profile JSON.")] = False
) -> None:
    """Utilities for working with agent profile configurations."""

    if template:
        sample = AgentProfile(
            identifier="cloud_engineer",
            name="Cloud Platform Engineer",
            description="Provisions infrastructure and automates deployment workflows.",
            goals=[
                "Ensure deployments are reproducible and observable.",
                "Optimize infrastructure cost without sacrificing reliability.",
            ],
            capabilities=[
                Capability(
                    name="provision_infra",
                    description="Generate Terraform IaC modules for new services.",
                    inputs={"service": "Name of the service", "region": "Cloud region"},
                    outputs={"module_path": "Filesystem path to generated module"},
                ),
            ],
        )
        typer.echo(json.dumps(sample.model_dump(mode="json"), indent=2))
        return

    typer.echo("No action requested. Use --template to generate a profile stub.")
