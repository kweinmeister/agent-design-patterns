"""Sequential Agent Pattern UI Registration."""

from fastapi import APIRouter, FastAPI
from pydantic import BaseModel

from patterns.sequential.agent import incident_triage_pipeline
from patterns.utils import (
    PatternConfig,
    PatternMetadata,
    configure_pattern,
    run_and_collect_history,
)


class RunRequest(BaseModel):
    """Request model for running the sequential agent."""

    input_text: str


def register(app: FastAPI) -> PatternMetadata:
    """Register the Sequential Agent pattern UI with the FastAPI application.

    Args:
        app: The FastAPI application instance.

    Returns:
        Metadata about the registered pattern.

    """
    router = APIRouter()

    @router.post("/sequential/run")
    async def run_pipeline(request: RunRequest) -> dict[str, str]:
        """Run the incident triage pipeline.

        Args:
            request: The run request containing input text.

        Returns:
            A dictionary containing the output text.

        """
        history = await run_and_collect_history(
            incident_triage_pipeline, request.input_text, "sequential_app"
        )
        # extracting the final message content
        if history:
            return {"output": history[-1]["content"]}
        return {"output": "No response generated."}

    return configure_pattern(
        app,
        router,
        PatternConfig(
            id="sequential",
            name="Sequential Agent",
            description="Executes a linear sequence of agents",
            icon="📋",
            base_file=__file__,
            template_name="sequential.html.j2",
            handler=None,
        ),
        agent=incident_triage_pipeline,
    )
