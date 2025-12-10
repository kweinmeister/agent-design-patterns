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


@pytest.mark.asyncio
async def test_p1_scenario_e2e() -> None:
    """Test Critical P1 scenario end-to-end."""
    input_text = "PaymentService failed with 500 error for User 123"
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

    if text_responses:
        result = text_responses[-1]
        # P1 Check
        assert "[URGENT]" in result or "Subject: [URGENT]" in result


@pytest.mark.asyncio
async def test_p3_scenario_e2e() -> None:
    """Test Minor P3 scenario end-to-end."""
    input_text = "The dashboard is loading slowly"
    app_name = "sequential_app"

    events = []
    async for event, _, _ in run_agent_standard(
        incident_triage_pipeline, input_text, app_name
    ):
        events.append(event)

    text_responses = [
        part.text
        for event in events
        if event.author == "IncidentCommunicator"
        and event.content
        and event.content.parts
        for part in event.content.parts
        if part.text
    ]

    if text_responses:
        result = text_responses[-1].lower()
        # P3 Check
        assert "for your information" in result or "fyi" in result


def test_registration() -> None:
    """Test that pattern can be registered without error."""
    app = FastAPI()
    meta = register(app)
    assert meta.id == "sequential"
    assert meta.name == "Sequential Agent"
    assert meta.demo_url == "/demo/sequential"
