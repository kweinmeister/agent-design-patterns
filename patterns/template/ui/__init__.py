"""UI integration for the Template pattern."""

from fastapi import APIRouter, FastAPI

from patterns.template.agent import root_agent
from patterns.utils import PatternConfig, PatternMetadata, configure_pattern

router = APIRouter()


def register(app: FastAPI) -> PatternMetadata:
    """Register the pattern."""
    return configure_pattern(
        app=app,
        router=router,
        agent=root_agent,
        config=PatternConfig(
            id="template",
            name="Template Pattern",
            description="A starting point for new patterns",
            icon="📝",
            base_file=__file__,
            handler=None,  # Handled by utils
            template_name="pattern.html.j2",
        ),
    )
