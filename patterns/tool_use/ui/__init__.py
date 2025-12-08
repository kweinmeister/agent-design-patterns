"""UI integration for the Tool Use pattern."""

from typing import Any

from fastapi import APIRouter, FastAPI

from patterns.tool_use.agent import root_agent
from patterns.utils import (
    PatternConfig,
    PatternMetadata,
    configure_pattern,
    run_and_collect_history,
)

router = APIRouter()


async def run_tool_use_agent(user_request: str) -> dict[str, Any]:
    """Run the tool use agent and capture the history."""
    history = await run_and_collect_history(root_agent, user_request, "tool_use_app")
    return {"history": history}


def register(app: FastAPI) -> PatternMetadata:
    """Register the pattern with the main application.

    Returns metadata about the pattern.
    """
    return configure_pattern(
        app=app,
        router=router,
        config=PatternConfig(
            id="tool_use",
            name="Tool Use",
            description="Demonstrates an agent that can use tools",
            icon="🛠️",
            base_file=__file__,
            handler=run_tool_use_agent,
            template_name="tool_use.html.j2",
            copilotkit_path="/copilotkit/tool_use",
        ),
    )
