"""UI integration for the Voting pattern."""

import asyncio
import json
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, FastAPI
from fastapi.responses import StreamingResponse
from google.adk.agents import BaseAgent

from patterns.utils import (
    PatternConfig,
    PatternMetadata,
    configure_pattern,
    run_agent_standard,
)
from patterns.voting.agent import (
    humorous_agent,
    judge_agent,
    professional_agent,
    urgent_agent,
)

router = APIRouter()


async def run_single_agent_to_queue(
    agent: BaseAgent, prompt: str, session_suffix: str, queue: asyncio.Queue, key: str
) -> str:
    """Run an agent and put its tokens into a queue. Return full text."""
    full_text = ""
    # We use a unique app_name/session for each to ensure isolation
    async for event, _, _ in run_agent_standard(
        agent, prompt, f"voting_{session_suffix}"
    ):
        if event.content and event.content.parts:
            part_text = event.content.parts[0].text
            if part_text:
                full_text += part_text
                await queue.put({"type": "step", "agent": key, "content": part_text})
    return full_text


async def stream_voting_generator(user_request: str) -> AsyncGenerator[str, None]:
    """Yield SSE events for the parallel voting process."""
    queue = asyncio.Queue()

    # 1. Start parallel generators
    # We use asyncio.create_task to run them in background
    tasks = [
        asyncio.create_task(
            run_single_agent_to_queue(
                humorous_agent, user_request, "humorous", queue, "humorous"
            )
        ),
        asyncio.create_task(
            run_single_agent_to_queue(
                professional_agent, user_request, "professional", queue, "professional"
            )
        ),
        asyncio.create_task(
            run_single_agent_to_queue(
                urgent_agent, user_request, "urgent", queue, "urgent"
            )
        ),
    ]

    async def producer_manager() -> None:
        """Wait for all tasks to complete and signal done."""
        await asyncio.gather(*tasks)
        await queue.put(None)  # Sentinel

    # Start manager in background
    _manager_task = asyncio.create_task(producer_manager())

    try:
        # 2. Consume queue until sentinel
        while True:
            item = await queue.get()
            if item is None:
                break
            yield f"data: {json.dumps(item)}\n\n"
            queue.task_done()
    finally:
        _manager_task.cancel()

    # 3. Retrieve results from tasks (they are already done)
    results = await asyncio.gather(*tasks)
    humorous_text, professional_text, urgent_text = results

    # 4. Construct judge prompt
    judge_prompt = f"""Original Product Description: {user_request}

---
Option 1 (Humorous Style):
{humorous_text}

---
Option 2 (Professional Style):
{professional_text}

---
Option 3 (Urgent Style):
{urgent_text}

---
Decide which option is best for a general audience."""

    # 5. Stream judge decision
    async for event, _, _ in run_agent_standard(judge_agent, judge_prompt, "judge"):
        if event.content and event.content.parts:
            part_text = event.content.parts[0].text
            if part_text:
                data = json.dumps(
                    {"type": "step", "agent": "judge", "content": part_text}
                )
                yield f"data: {data}\n\n"

    yield f"data: {json.dumps({'type': 'complete'})}\n\n"


@router.get("/stream_voting")
async def stream_voting(prompt: str) -> StreamingResponse:
    """Stream the voting agent's execution."""
    return StreamingResponse(
        stream_voting_generator(prompt), media_type="text/event-stream"
    )


async def run_voting_agent(_user_request: str) -> dict[str, Any]:
    """Run the parallel generation and voting process.

    Kept for compatibility with PatternConfig handler.
    If JS is enabled, this might not be used directly if form submission is prevented.
    """
    return {"message": "Use streaming endpoint"}


def register(app: FastAPI) -> PatternMetadata:
    """Register the pattern."""
    return configure_pattern(
        app=app,
        router=router,
        config=PatternConfig(
            id="voting",
            name="Voting",
            description=(
                "Generates multiple options in parallel and selects the best one"
            ),
            icon="🗳️",
            base_file=__file__,
            handler=run_voting_agent,
            template_name="voting.html.j2",
            copilotkit_path="/copilotkit/voting",
        ),
    )
