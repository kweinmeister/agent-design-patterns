"""UI integration for the Template pattern."""

from fastapi import APIRouter, FastAPI

from patterns.template.agent import root_agent
from patterns.utils import (
    PatternConfig,
    PatternMetadata,
    configure_pattern,
    run_agent_standard,
)

router = APIRouter()


async def run_template_agent(user_request: str) -> str:
    """Run the agent."""
    response_text = ""
    async for event, _, _ in run_agent_standard(
        root_agent, user_request, "template_app"
    ):
        if event.content and event.content.parts:
            text = event.content.parts[0].text
            if text:
                response_text += text

    return response_text


def register(app: FastAPI) -> PatternMetadata:
    """Register the pattern."""
    return configure_pattern(
        app=app,
        router=router,
        config=PatternConfig(
            id="template",
            name="Template Pattern",
            description="A starting point for new patterns",
            icon="📝",
            base_file=__file__,
            handler=run_template_agent,
            template_name="pattern.html.j2",
            copilotkit_path="/copilotkit/template",
        ),
    )
