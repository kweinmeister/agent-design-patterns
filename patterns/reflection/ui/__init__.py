"""UI integration for the Reflection pattern."""

from fastapi import APIRouter, FastAPI
from fastapi.responses import StreamingResponse

from patterns.reflection.agent import root_agent
from patterns.utils import (
    PatternConfig,
    PatternMetadata,
    configure_pattern,
    stream_agent_events,
)

router = APIRouter()


@router.get("/stream_reflection")
async def stream_reflection(prompt: str) -> StreamingResponse:
    """Stream the reflection agent's execution."""
    return StreamingResponse(
        stream_agent_events(root_agent, prompt, "reflection_app"),
        media_type="text/event-stream",
    )


def register(app: FastAPI) -> PatternMetadata:
    """Register the pattern with the main application.

    Returns metadata about the pattern.
    """
    return configure_pattern(
        app=app,
        router=router,
        agent=root_agent,
        config=PatternConfig(
            id="reflection",
            name="Reflection",
            description="An agent that critiques and refines its own work",
            icon="🤔",
            base_file=__file__,
            handler=None,  # Handled by utils
            template_name="reflection.html.j2",
        ),
    )
