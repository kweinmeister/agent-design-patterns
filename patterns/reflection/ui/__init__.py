"""UI integration for the Reflection pattern."""

from typing import Any

from fastapi import APIRouter, FastAPI

from patterns.reflection.agent import STATE_CURRENT_DOC, root_agent
from patterns.utils import PatternUI

router = APIRouter()


class ReflectionUI(PatternUI):
    """UI integration for the Reflection pattern."""

    def __init__(self) -> None:
        """Initialize the ReflectionUI."""
        super().__init__(
            pattern_id="reflection",
            name="Reflection",
            description="Critiques and refines its own output to improve quality",
            icon="🪞",
            agent=root_agent,
            current_file=__file__,
            template_name="reflection.html",
        )

    async def run_agent(self, user_request: str) -> dict[str, Any]:
        """Run the reflection loop agent and capture the history."""
        history = []
        final_doc = ""
        current_runner = None
        current_session_id = None

        async for event, runner, session_id in self.run_agent_generator(user_request):
            if event.content and event.content.parts:
                text = event.content.parts[0].text
                if text:
                    history.append({"role": event.author, "content": text})

            current_runner = runner
            current_session_id = session_id

        # Get final state
        if history and current_runner and current_session_id:
            session = await current_runner.session_service.get_session(
                app_name=self.app_name,
                user_id="user",
                session_id=current_session_id,
            )
            final_doc = session.state.get(STATE_CURRENT_DOC, "") if session else ""

        return {"final": final_doc, "history": history}


pattern_ui = ReflectionUI()


def register(app: FastAPI) -> dict[str, str]:
    """Register the pattern with the main application.

    Returns metadata about the pattern.
    """
    return pattern_ui.register(app, copilotkit_path="/copilotkit/reflection")
