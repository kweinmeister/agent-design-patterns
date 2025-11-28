"""Tests for the Tool Use Agent."""

import asyncio

import pytest
from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part

from patterns.tool_use.agent import root_agent


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

    # We need to consume the generator
    history = [
        {
            "role": event.author,
            "content": (event.content.parts[0].text or "")
            if event.content.parts
            else "",
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

    # Check if the answer is correct (approximate check since LLM output varies)
    # We look for the result of 123 * 456 which is 56088
    expected_result = "56088"
    found_answer = False
    for item in history:
        if expected_result in item["content"]:
            found_answer = True
            break

    assert found_answer, "Agent did not provide the correct calculation result"


if __name__ == "__main__":
    asyncio.run(test_tool_use_agent())
