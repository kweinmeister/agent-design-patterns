"""UI integration for the Reflection pattern."""

import json
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, FastAPI
from fastapi.responses import StreamingResponse

from patterns.reflection.agent import STATE_CURRENT_DOC, root_agent
from patterns.utils import (
    PatternConfig,
    PatternMetadata,
    configure_pattern,
    run_agent_standard,
)

router = APIRouter()


async def generate_reflection_steps(
    user_request: str,
) -> AsyncGenerator[dict[str, Any], None]:
    """Shared generator that yields agent steps and the final result."""
    current_runner = None
    current_session_id = None

    async for event, runner, session_id in run_agent_standard(
        root_agent, user_request, "reflection_app"
    ):
        current_runner = runner
        current_session_id = session_id

        if event.content and event.content.parts:
            text = event.content.parts[0].text
            if text:
                yield {"type": "step", "role": event.author, "content": text}

    # Get final state
    if current_runner and current_session_id:
        session = await current_runner.session_service.get_session(
            app_name="reflection_app",
            user_id="user",
            session_id=current_session_id,
        )
        final_doc = session.state.get(STATE_CURRENT_DOC, "") if session else ""
        if final_doc:
            yield {"type": "final", "content": final_doc}


async def run_reflection_agent(user_request: str) -> dict[str, Any]:
    """Run the reflection loop agent and capture the history.

    Note: This is kept for backward compatibility and non-streaming use cases.
    """
    history = []
    final_doc = ""

    async for item in generate_reflection_steps(user_request):
        if item["type"] == "step":
            history.append({"role": item["role"], "content": item["content"]})
        elif item["type"] == "final":
            final_doc = item["content"]

    return {"final": final_doc, "history": history}


@router.get("/stream_reflection")
async def stream_reflection(prompt: str) -> StreamingResponse:
    """Stream the reflection agent's execution."""
    return StreamingResponse(event_generator(prompt), media_type="text/event-stream")


async def event_generator(user_request: str) -> AsyncGenerator[str, None]:
    """Yield events from the agent in SSE format."""
    async for item in generate_reflection_steps(user_request):
        if item["type"] == "step":
            data = json.dumps({"role": item["role"], "content": item["content"]})
            yield f"data: {data}\n\n"
        elif item["type"] == "final":
            data = json.dumps({"role": "final", "content": item["content"]})
            yield f"data: {data}\n\n"


def register(app: FastAPI) -> PatternMetadata:
    """Register the pattern with the main application.

    Returns metadata about the pattern.
    """
    return configure_pattern(
        app=app,
        router=router,
        config=PatternConfig(
            id="reflection",
            name="Reflection",
            description="An agent that critiques and refines its own work",
            icon="🤔",
            base_file=__file__,
            handler=run_reflection_agent,
            template_name="reflection.html.j2",
            copilotkit_path="/copilotkit/reflection",
        ),
    )
