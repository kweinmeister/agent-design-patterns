"""UI integration for the Human-in-the-Loop pattern."""

from typing import Any

from fastapi import APIRouter, FastAPI
from pydantic import BaseModel

from patterns.human_in_the_loop.agent import hitl_agent
from patterns.utils import (
    PatternConfig,
    PatternMetadata,
    configure_pattern,
    run_agent_standard,
)

router = APIRouter()


class HitlRequest(BaseModel):
    """Request model for HITL interaction."""

    prompt: str
    session_id: str | None = None


async def run_hitl_agent(request: HitlRequest) -> dict[str, Any]:
    """Run the agent and collect history."""
    history = []
    requires_confirmation = False
    app_name = "hitl_app"

    input_content = request.prompt

    async for event, _, _ in run_agent_standard(
        hitl_agent, input_content, app_name, request.session_id
    ):
        if event.content and event.content.parts:
            # Collect text history
            history.extend(
                {"role": event.author, "content": part.text}
                for part in event.content.parts
                if part.text
            )

            # Check for specific tool calls that trigger confirmation
            # In this pattern, 'publish_press_release' is configured to require it.
            # If the model emits this function call, the runner (in a real scenario)
            # would pause. Use this event as the robust signal for the UI.
            for part in event.content.parts:
                if (
                    part.function_call
                    and part.function_call.name == "publish_press_release"
                ):
                    requires_confirmation = True

    return {"history": history, "requires_confirmation": requires_confirmation}


def register(app: FastAPI) -> PatternMetadata:
    """Register the pattern."""

    @router.post("/hitl/run")
    async def run_hitl(request: HitlRequest) -> dict[str, Any]:
        return await run_hitl_agent(request)

    # CopilotKit Adapter
    async def standard_handler(prompt: str) -> dict[str, str]:
        """Adapter for CopilotKit which expects string output."""
        # For the simple copilot case, we just run it and return the last text
        # This loses the rich UI approval control but allows basic text interaction
        result = await run_hitl_agent(HitlRequest(prompt=prompt))
        history = result.get("history", [])
        if history:
            return {"response": history[-1]["content"]}
        return {"response": ""}

    return configure_pattern(
        app=app,
        router=router,
        config=PatternConfig(
            id="human_in_the_loop",
            name="Human in the Loop",
            description="Intervention pattern requiring human approval before action",
            icon="🛑",
            base_file=__file__,
            handler=standard_handler,  # Use the adapter here
            template_name="hitl.html.j2",
            copilotkit_path="/copilotkit/hitl",
        ),
    )
