"""Unit tests for the Sequential Agent Pattern."""

import pytest
from fastapi import FastAPI
from google.adk.agents import SequentialAgent

from patterns.sequential.agent import incident_triage_pipeline
from patterns.sequential.ui import register
from patterns.utils import run_agent_standard


@pytest.fixture
def agent() -> SequentialAgent:
    """Return the incident triage pipeline agent."""
    return incident_triage_pipeline


def test_pipeline_structure(agent: SequentialAgent) -> None:
    """Verifies the pipeline has 3 steps in the correct order."""
    assert len(agent.sub_agents) == 3  # noqa: PLR2004
    assert agent.sub_agents[0].name == "IncidentExtractor"
    assert agent.sub_agents[1].name == "IncidentAssessor"
    assert agent.sub_agents[2].name == "IncidentCommunicator"


@pytest.mark.parametrize(
    ("input_text", "checks", "case_sensitive"),
    [
        (
            "PaymentService failed with 500 error for User 123",
            ["[URGENT]", "Subject: [URGENT]"],
            True,
        ),
        (
            "The dashboard is loading slowly",
            ["for your information", "fyi"],
            False,
        ),
    ],
)
@pytest.mark.asyncio
async def test_e2e_scenarios(
    input_text: str,
    checks: list[str],
    case_sensitive: bool,  # noqa: FBT001
) -> None:
    """Test various scenarios end-to-end."""
    app_name = "sequential_app"

    events = []
    async for event, _, _ in run_agent_standard(
        incident_triage_pipeline, input_text, app_name
    ):
        events.append(event)

    # Get final text response
    text_responses = [
        part.text
        for event in events
        if event.author == "IncidentCommunicator"
        and event.content
        and event.content.parts
        for part in event.content.parts
        if part.text
    ]

    assert text_responses, "No response from IncidentCommunicator"
    result = text_responses[-1]
    if not case_sensitive:
        result = result.lower()

    assert any(check in result for check in checks)


def test_registration() -> None:
    """Test that pattern can be registered without error."""
    app = FastAPI()
    meta = register(app)
    assert meta.id == "sequential"
    assert meta.name == "Sequential Agent"
    assert meta.demo_url == "/demo/sequential"
