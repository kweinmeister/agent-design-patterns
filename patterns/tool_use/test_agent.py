"""Tests for the Tool Use Agent."""

import asyncio

import pytest
from fastapi import FastAPI
from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part

from patterns.tool_use.agent import root_agent
from patterns.tool_use.ui import register


@pytest.mark.asyncio
async def test_tool_use_agent() -> None:
    """Test the tool use agent with a calculation request."""
    user_request = "What is 123 * 456?"

    app_name = "tool_use_app"
    runner = InMemoryRunner(agent=root_agent, app_name=app_name)

    # Create session explicitly
    await runner.session_service.create_session(
        app_name=app_name,
        user_id="test_user",
        session_id="test_session",
    )

    # Run the agent
    history = [
        event
        async for event in runner.run_async(
            user_id="test_user",
            session_id="test_session",
            new_message=Content(parts=[Part(text=user_request)]),
        )
    ]
    assert history, "History should not be empty"

    # Check that we got a response from the model
    # The author is the agent name, e.g. "ToolUseAgent"
    model_responses = [
        event
        for event in history
        if event.author in ("ToolUseAgent", "model") and event.content
    ]
    assert model_responses, "Agent did not provide a response"


if __name__ == "__main__":
    asyncio.run(test_tool_use_agent())


def test_tool_use_registration() -> None:
    """Test that Tool Use pattern can be registered without error."""
    app = FastAPI()
    meta = register(app)
    assert meta.id == "tool_use"
    assert meta.name == "Tool Use"
    assert meta.demo_url == "/demo/tool_use"
