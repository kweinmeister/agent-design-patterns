"""UI integration for the Tool Use pattern."""

from typing import Any

from fastapi import APIRouter, FastAPI

from patterns.tool_use.agent import root_agent
from patterns.utils import configure_pattern, run_agent_standard

router = APIRouter()


async def run_tool_use_agent(user_request: str) -> dict[str, Any]:
    """Run the tool use agent and capture the history."""
    history = []

    async for event, _, _ in run_agent_standard(
        root_agent, user_request, "tool_use_app"
    ):
        if event.content and event.content.parts:
            text = event.content.parts[0].text
            if text:
                history.append({"role": event.author, "content": text})

    return {"history": history}


def register(app: FastAPI) -> dict[str, str]:
    """Register the pattern with the main application.

    Returns metadata about the pattern.
    """
    return configure_pattern(
        app=app,
        router=router,
        pattern_id="tool_use",
        name="Tool Use",
        description="Uses external tools to perform tasks",
        icon="🛠️",
        base_file=__file__,
        handler=run_tool_use_agent,
        template_name="tool_use.html.j2",
        copilotkit_path="/copilotkit/tool_use",
    )
