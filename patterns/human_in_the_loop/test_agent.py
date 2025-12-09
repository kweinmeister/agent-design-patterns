"""Tests for the Human-in-the-Loop Agent."""

import pytest
from fastapi import FastAPI

from patterns.human_in_the_loop.agent import hitl_agent
from patterns.human_in_the_loop.ui import register
from patterns.utils import run_agent_standard


@pytest.mark.asyncio
async def test_hitl_agent_approval_flow() -> None:
    """Test the HITL agent flow from draft to approval."""
    # 1. Request Draft
    app_name = "hitl_test_app"
    session_id = "session_1"

    draft_prompt = (
        "Draft a press release for Project X, "
        "a revolutionary coffee-flavored toothpaste. It launches tomorrow."
    )

    history: list[str] = []
    async for event, _, _ in run_agent_standard(
        hitl_agent, draft_prompt, app_name, session_id
    ):
        if event.content and event.content.parts:
            history.extend([part.text for part in event.content.parts if part.text])

    assert history, "Agent should produce a draft"

    # 2. User requests to publish (Triggering the tool call)
    # The agent instructions say "Once the user is satisfied... publish it".
    # So we must explicitly tell it to publish.
    function_calls = []
    async for event, _, _ in run_agent_standard(
        hitl_agent, "Looks good. Publish it.", app_name, session_id
    ):
        if event.content and event.content.parts:
            function_calls.extend(
                [
                    part.function_call
                    for part in event.content.parts
                    if part.function_call
                ]
            )

    # User asked to publish. The agent should try to call the tool.
    # We won't necessarily see "SUCCESS" yet if we haven't mocked the confirmation
    # flow fully or if the runner halts for confirmation before returning output.
    # But we SHOULD see the FunctionCall itself.
    assert function_calls, "Agent should attempt to call a tool"
    assert function_calls[0].name == "publish_press_release"

    # 3. Confirm
    # We send the confirmation and verify the agent proceeds to publish.
    final_history: list[str] = []
    async for event, _, _ in run_agent_standard(
        hitl_agent, '{"confirmed": true}', app_name, session_id
    ):
        if event.content and event.content.parts:
            final_history.extend(
                [part.text for part in event.content.parts if part.text]
            )

    # Assert that the agent confirmed the successful publication.
    # We check for keywords indicating success. The exact wording depends on the
    # model's generation.
    assert any(
        "published" in message.lower() or "success" in message.lower()
        for message in final_history
    ), f"Agent should confirm successful publication. History: {final_history}"


def test_hitl_registration() -> None:
    """Test that HITL pattern can be registered without error."""
    app = FastAPI()
    meta = register(app)
    assert meta.id == "human_in_the_loop"
    assert meta.name == "Human in the Loop"
