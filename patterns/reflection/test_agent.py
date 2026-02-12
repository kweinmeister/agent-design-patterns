"""Tests for the Reflection Agent."""

import asyncio
import json

import pytest
from fastapi import FastAPI
from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part

from patterns.reflection.agent import STATE_CURRENT_DOC, root_agent
from patterns.reflection.ui import register
from patterns.utils import stream_agent_events


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

    final_doc = session.state.get(STATE_CURRENT_DOC, "")
    assert final_doc, "Current document should not be empty"
    assert isinstance(final_doc, str), "Current document should be a string"


if __name__ == "__main__":
    asyncio.run(test_reflection_loop())


@pytest.mark.asyncio
async def test_reflection_streaming_endpoint() -> None:
    """Test the streaming endpoint returns SSE events."""
    user_request = "Write a haiku about Python."

    # Run the generator
    events = [
        event
        async for event in stream_agent_events(
            root_agent,
            user_request,
            "reflection_app",
        )
    ]

    assert len(events) > 0, "Should receive events"

    # Check format of events
    has_final = False
    for event in events:
        assert event.startswith("data: "), "Event should start with data:"
        assert event.endswith("\n\n"), "Event should end with double newline"

        # Verify JSON content
        json_str = event[6:].strip()
        data = json.loads(json_str)
        assert "type" in data

        if data["type"] == "step":
            assert "role" in data
            assert "content" in data
        elif data["type"] == "complete":
            has_final = True
            assert "final" in data

    assert has_final, "Should receive complete event"


def test_reflection_registration() -> None:
    """Test that Reflection pattern can be registered without error."""
    app = FastAPI()
    meta = register(app)
    assert meta.id == "reflection"
    assert meta.name == "Reflection"
    assert meta.demo_url == "/demo/reflection"
