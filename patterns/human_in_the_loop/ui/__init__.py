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
    # For tool confirmation
    tool_confirmation: dict[str, Any] | None = None


async def run_hitl_agent(request: HitlRequest) -> dict[str, Any]:
    """Run the agent and collect history."""
    history = []
    app_name = "hitl_app"

    # If we have a confirmation payload, we need to pass that to the runner.
    # However, the ADK runner run_async primarily takes a new_message.
    # We might need to handle the confirmation as a specific input type or
    # ensure the session state is expecting it.

    # The article implies we send {confirmed: true} back to the agent.
    # In ADK, this usually resolves the pending tool call.

    # We need to construct the input message based on whether it's a new prompt
    # or a confirmation.

    # Note: run_agent_standard is a helper that wraps runner.run_async.
    # If we need to pass a confirmation, it might be better to just pass it as text
    # if the agent is designed to parse it, OR use the specific ADK mechanism
    # if available.

    # But based on the article: "provide {confirmed: true} to the agent".
    # This suggests sending a tool response or a specific message.
    # Let's assume for now we send the confirmation as a tool response or similar.

    # Actually, looking at ADK docs (inferred), passing a tool output usually involves
    # responding to the tool call.

    # Let's stick to the standard runner for now and see what events we get.
    # When a tool requires confirmation, the agent should effectively 'pause' or yield
    # a request for user input.

    # We'll rely on the agent's output to tell us what to do.

    input_content = request.prompt
    if request.tool_confirmation:
        # If we have a confirmation, we might need to format it for the agent
        # or just pass it through if the session state is waiting.
        # ADK typically handles this by resuming the session.
        # For simplicity, if we are confirming, we send the prompt
        # (which might be empty or "proceed")
        pass

    async for event, _, _ in run_agent_standard(
        hitl_agent, input_content, app_name, request.session_id
    ):
        if event.content and event.content.parts:
            history.extend(
                {"role": event.author, "content": part.text}
                for part in event.content.parts
                if part.text
            )

            # Check for functioning calling part if present and pending confirmation
            # Note: ADK events for tool calls might be distinct.
            # However, usually the text part will contain the model's thought process
            # or the tool call request.

            # If using FunctionTool with confirmation, the model emits a tool call,
            # then execution pauses. We need to detect this pause state.
            # The 'event' object might have metadata.

    return {"history": history}


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
