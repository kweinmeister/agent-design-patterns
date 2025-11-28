"""Tests for the Hello World Agent."""

import asyncio

import pytest
from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part

from patterns.template.agent import root_agent


@pytest.mark.asyncio
async def test_hello_world_agent() -> None:
    """Test the hello world agent."""
    user_request = "Hello, world!"

    app_name = "template_app"
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


if __name__ == "__main__":
    asyncio.run(test_hello_world_agent())
