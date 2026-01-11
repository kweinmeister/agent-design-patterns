"""UI integration for the Human-in-the-Loop pattern."""

from typing import Any

from fastapi import APIRouter, FastAPI
from pydantic import BaseModel

from patterns.human_in_the_loop.agent import SUCCESS_MSG, hitl_agent
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
    history: list[dict[str, str]] = []
    requires_confirmation = False
    is_published = False
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

            # Check confirmed tools.
            for part in event.content.parts:
                if not part.function_call:
                    continue

                # Iterate agent tools to find matching function name and config.
                for tool in hitl_agent.tools:
                    # In ADK, tools can be FunctionTool or others.
                    # We check for `name` attribute safely.
                    tool_name = getattr(tool, "name", None)
                    # we try to be safer.
                    if (
                        tool_name == part.function_call.name
                        and hasattr(tool, "_require_confirmation")
                        and tool._require_confirmation  # noqa: SLF001
                    ):
                        requires_confirmation = True
                        break

                if requires_confirmation:
                    break

        # Check for successful publication in the history
        if (
            event.content
            and event.content.parts
            and any(
                SUCCESS_MSG in part.text for part in event.content.parts if part.text
            )
        ):
            is_published = True

    return {
        "history": history,
        "requires_confirmation": requires_confirmation,
        "is_published": is_published,
    }


def register(app: FastAPI) -> PatternMetadata:
    """Register the pattern."""

    @router.post("/hitl/run")
    async def run_hitl(request: HitlRequest) -> dict[str, Any]:
        return await run_hitl_agent(request)

    return configure_pattern(
        app=app,
        router=router,
        config=PatternConfig(
            id="human_in_the_loop",
            name="Human in the Loop",
            description="Intervention pattern requiring human approval before action",
            icon="🛑",
            base_file=__file__,
            handler=web_handler,
            template_name="hitl.html.j2",
        ),
    )


async def web_handler(prompt: str) -> dict[str, Any]:
    """Execute the agent for the web interface request."""
    return await run_hitl_agent(HitlRequest(prompt=prompt))
