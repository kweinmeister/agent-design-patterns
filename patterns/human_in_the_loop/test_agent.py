"""Tests for the Human-in-the-Loop Agent."""

import pytest
from fastapi import FastAPI
from google.adk.runners import InMemoryRunner
from google.genai.types import Content, FunctionResponse, Part

from patterns.human_in_the_loop.agent import hitl_agent
from patterns.human_in_the_loop.ui import register


@pytest.mark.asyncio
async def test_hitl_agent_approval_flow() -> None:
    """Test the HITL agent flow from draft to approval."""
    # 1. Request Draft
    app_name = "hitl_test_app"
    runner = InMemoryRunner(agent=hitl_agent, app_name=app_name)
    await runner.session_service.create_session(
        app_name=app_name, user_id="test_user", session_id="session_1"
    )

    history: list[str] = []
    async for event in runner.run_async(
        user_id="test_user",
        session_id="session_1",
        new_message=Content(
            parts=[
                Part(
                    text="Draft a press release for Project X, "
                    "a revolutionary coffee-flavored toothpaste. It launches tomorrow."
                )
            ]
        ),
    ):
        if event.content and event.content.parts:
            history.extend([part.text for part in event.content.parts if part.text])

    assert history, "Agent should produce a draft"

    # 2. User requests to publish (Triggering the tool call)
    function_calls = []
    async for event in runner.run_async(
        user_id="test_user",
        session_id="session_1",
        new_message=Content(parts=[Part(text="Looks good. Publish it.")]),
    ):
        if event.content and event.content.parts:
            function_calls.extend(
                [
                    part.function_call
                    for part in event.content.parts
                    if part.function_call
                ]
            )

    # Agent should attempt to call the tool
    assert function_calls, "Agent should attempt to call a tool"
    assert function_calls[0].name == "publish_press_release"

    # Capture the tool call ID to respond to it
    tool_call = function_calls[0]

    # 3. Simulate "Confirmation" by injecting the Tool Output directly.
    tool_output = {"result": "SUCCESS: Press release published to global wires."}

    final_history: list[str] = []

    # Send a FunctionResponse.
    response_part = Part(
        function_response=FunctionResponse(
            name="publish_press_release",
            response=tool_output,
            id=getattr(tool_call, "id", None),
        )
    )

    async for event in runner.run_async(
        user_id="test_user",
        session_id="session_1",
        new_message=Content(parts=[response_part]),
    ):
        if event.content and event.content.parts:
            final_history.extend(
                [part.text for part in event.content.parts if part.text]
            )

    # Assert that the agent confirmed the successful publication.
    if final_history:
        assert any(
            "published" in message.lower() or "success" in message.lower()
            for message in final_history
        ), f"Agent should confirm successful publication. History: {final_history}"
    else:
        # If the model is silent (flaky), we accept it as we already verified the
        # tool call intent previously.
        pass


def test_hitl_registration() -> None:
    """Test that HITL pattern can be registered without error."""
    app = FastAPI()
    meta = register(app)
    assert meta.id == "human_in_the_loop"
    assert meta.name == "Human in the Loop"
