"""Tests for the Reflection Agent."""

import asyncio

import pytest
from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part

from patterns.reflection.agent import STATE_CURRENT_DOC, root_agent


@pytest.mark.asyncio
async def test_reflection_loop() -> None:
    """Test the reflection loop agent."""
    user_request = "Write a haiku about rust."

    app_name = "reflection_app"
    runner = InMemoryRunner(agent=root_agent, app_name=app_name)

    # Create session explicitly
    await runner.session_service.create_session(
        app_name=app_name,
        user_id="test_user",
        session_id="test_session",
    )

    # We need to consume the generator
    history = [
        {
            "role": event.author,
            "content": event.content.parts[0].text if event.content.parts else "",
        }
        async for event in runner.run_async(
            user_id="test_user",
            session_id="test_session",
            new_message=Content(
                parts=[Part(text=user_request)],
            ),
        )
        if event.content
    ]
    assert history, "History should not be empty"

    # Get state from session service
    session = await runner.session_service.get_session(
        app_name=runner.app_name,
        user_id="test_user",
        session_id="test_session",
    )
    if session is None:
        msg = "Session is None"
        raise ValueError(msg)

    # Verify we have the expected roles in the history
    roles = {step["role"] for step in history}
    assert "InitialWriterAgent" in roles, "Should have initial writer step"
    assert "CriticAgent" in roles, "Should have critic step"
    assert "RefinerAgent" in roles, "Should have refiner step"

    assert session.state.get(STATE_CURRENT_DOC, "") == history[-1]["content"]


if __name__ == "__main__":
    asyncio.run(test_reflection_loop())
