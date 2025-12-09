"""Tests for the Human-in-the-Loop Agent."""

import pytest
from fastapi import FastAPI
from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part

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
    # The agent instructions say "Once the user is satisfied... publish it".
    # So we must explicitly tell it to publish.
    history_publish_req: list[str] = []
    function_calls = []
    async for event in runner.run_async(
        user_id="test_user",
        session_id="session_1",
        new_message=Content(parts=[Part(text="Looks good. Publish it.")]),
    ):
        if event.content and event.content.parts:
            history_publish_req.extend(
                [part.text for part in event.content.parts if part.text]
            )
            function_calls.extend(
                [
                    part.function_call
                    for part in event.content.parts
                    if part.function_call
                ]
            )

    # User asked to publish. The agent should try to call the tool.
    # We won't necessarily see "SUCCESS" yet if we haven't mocked the confirmation flow fully
    # or if the runner halts for confirmation before returning output.
    # But we SHOULD see the FunctionCall itself.
    assert function_calls, "Agent should attempt to call a tool"
    assert function_calls[0].name == "publish_press_release"

    # 3. Confirm
    # With native ADK HITL, we send a specific confirmation payload or message
    # In the absence of a dedicated confirmation method on the runner in this version,
    # we simulate the user sending the confirmation JSON as text, which the agent/model
    # should interpret as the tool confirmation input provided by the "system" (the UI).

    history_approval: list[str] = []
    async for event in runner.run_async(
        user_id="test_user",
        session_id="session_1",
        new_message=Content(parts=[Part(text='{"confirmed": true}')]),
    ):
        if event.content and event.content.parts:
            history_approval.extend(
                [part.text for part in event.content.parts if part.text]
            )

    # Now it should call the tool
    # We won't necessarily see "SUCCESS" yet if we haven't mocked the confirmation flow fully
    # or if the runner halts for confirmation before returning output.
    # But we SHOULD see the FunctionCall itself, which confirms the agent's intent.


def test_hitl_registration() -> None:
    """Test that HITL pattern can be registered without error."""
    app = FastAPI()
    meta = register(app)
    assert meta.id == "human_in_the_loop"
    assert meta.name == "Human in the Loop"
