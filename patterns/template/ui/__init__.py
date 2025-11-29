"""UI integration for the Template pattern."""

from fastapi import APIRouter, FastAPI

from patterns.template.agent import root_agent
from patterns.utils import PatternUI

router = APIRouter()


class TemplateUI(PatternUI):
    """UI integration for the Template pattern."""

    def __init__(self) -> None:
        """Initialize the TemplateUI."""
        super().__init__(
            pattern_id="template",
            name="Template Pattern",
            description="A template for creating new patterns.",
            icon="📝",
            agent=root_agent,
            current_file=__file__,
            template_name="pattern.html.j2",
        )

    async def run_agent(self, user_request: str) -> str:
        """Run the agent."""
        response_text = ""
        async for event, _, _ in self.run_agent_generator(user_request):
            if event.content and event.content.parts:
                text = event.content.parts[0].text
                if text:
                    response_text += text

        return response_text


pattern_ui = TemplateUI()


def register(app: FastAPI) -> dict[str, str]:
    """Register the pattern."""
    return pattern_ui.register(app)
