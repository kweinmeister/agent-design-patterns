"""UI integration for the Tool Use pattern."""

from typing import Any

from fastapi import APIRouter, FastAPI

from patterns.tool_use.agent import root_agent
from patterns.utils import PatternUI

router = APIRouter()


class ToolUseUI(PatternUI):
    """UI integration for the Tool Use pattern."""

    def __init__(self) -> None:
        """Initialize the ToolUseUI."""
        super().__init__(
            pattern_id="tool_use",
            name="Tool Use",
            description="Uses external tools to perform tasks",
            icon="🛠️",
            agent=root_agent,
            current_file=__file__,
            template_name="tool_use.html",
        )

    async def run_agent(self, user_request: str) -> dict[str, Any]:
        """Run the tool use agent and capture the history."""
        history = []

        async for event, _, _ in self.run_agent_generator(user_request):
            if event.content and event.content.parts:
                text = event.content.parts[0].text
                if text:
                    history.append({"role": event.author, "content": text})

        return {"history": history}


pattern_ui = ToolUseUI()


def register(app: FastAPI) -> dict[str, str]:
    """Register the pattern with the main application.

    Returns metadata about the pattern.
    """
    return pattern_ui.register(app, copilotkit_path="/copilotkit/tool_use")
