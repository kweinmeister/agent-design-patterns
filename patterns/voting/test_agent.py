"""Tests for the Voting Pattern."""

import pytest

from patterns.voting.agent import (
    humorous_agent,
    judge_agent,
    professional_agent,
    urgent_agent,
)


@pytest.mark.asyncio
async def test_agent_definitions() -> None:
    """Test that agents are correctly instantiated with expected names."""
    assert humorous_agent.name == "HumorousAgent"
    assert professional_agent.name == "ProfessionalAgent"
    assert urgent_agent.name == "UrgentAgent"
    assert judge_agent.name == "JudgeAgent"


@pytest.mark.asyncio
async def test_instructions_exist() -> None:
    """Ensure all agents have instructions."""
    # The current ADK version might store instructions in different attributes depending
    # on the class, but LlmAgent typically has it. We check if it's not empty.
    # Accessing public attribute instruction for testing purposes
    assert humorous_agent.instruction, "Humorous agent missing instruction"
    assert professional_agent.instruction, "Professional agent missing instruction"
    assert urgent_agent.instruction, "Urgent agent missing instruction"
    assert judge_agent.instruction, "Judge agent missing instruction"
