"""UI integration for the Orchestrator pattern."""

import asyncio
import json
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, FastAPI
from fastapi.responses import StreamingResponse

from patterns.orchestrator.agent import (
    create_worker_agent,
    orchestrator_agent,
    synthesizer_agent,
)
from patterns.utils import (
    PatternConfig,
    PatternMetadata,
    configure_pattern,
    parse_json_from_text,
    run_agent_standard,
)

router = APIRouter()


async def run_worker_to_queue(
    worker_name: str,
    worker_instruction: str,
    user_request: str,
    queue: asyncio.Queue,
    task_id: int,
) -> str:
    """Run a specialized worker and stream its progress."""
    full_text = ""
    worker = create_worker_agent(worker_name, worker_instruction)

    # Notify that worker has started
    await queue.put({"type": "worker_start", "task_id": task_id, "name": worker_name})

    prompt = (
        f"Original Request: {user_request}\n\nYour specific task: {worker_instruction}"
    )

    async for event, _, _ in run_agent_standard(worker, prompt, f"worker_{task_id}"):
        if event.content and event.content.parts:
            part_text = event.content.parts[0].text
            if part_text:
                full_text += part_text
                await queue.put(
                    {"type": "worker_step", "task_id": task_id, "content": part_text}
                )

    await queue.put({"type": "worker_complete", "task_id": task_id, "final": full_text})
    return full_text


async def stream_orchestrator_generator(user_request: str) -> AsyncGenerator[str, None]:
    """Orchestration loop: Plan -> Parallel Workers -> Synthesis."""
    queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()

    # 1. Planning phase
    await queue.put({"type": "status", "message": "Planning the orchestration..."})

    plan_json = None
    async for event, _, _ in run_agent_standard(
        orchestrator_agent, user_request, "orchestrator_plan"
    ):
        if event.is_final_response() and event.author == orchestrator_agent.name:
            if event.content and event.content.parts:
                # When output_schema is used, the final event's text is the JSON
                text = "".join(p.text for p in event.content.parts if p.text)
                if text:
                    plan_json = parse_json_from_text(text)

    if not plan_json:
        await queue.put({"type": "error", "message": "Failed to generate plan."})
        yield f"data: {json.dumps({'type': 'complete'})}\n\n"
        return

    await queue.put({"type": "plan", "plan": plan_json})

    # 2. Worker phase
    tasks = []
    for i, task in enumerate(plan_json.get("tasks", [])):
        tasks.append(
            asyncio.create_task(
                run_worker_to_queue(
                    task["title"], task["description"], user_request, queue, i
                )
            )
        )

    async def producer_manager() -> None:
        try:
            await asyncio.gather(*tasks)
        finally:
            await queue.put(None)

    _manager_task = asyncio.create_task(producer_manager())

    try:
        while True:
            item = await queue.get()
            if item is None:
                break
            yield f"data: {json.dumps(item)}\n\n"
            queue.task_done()
    finally:
        _manager_task.cancel()

    # Retrieve worker results
    worker_outputs = await asyncio.gather(*tasks)

    # 3. Synthesis phase
    await queue.put({"type": "status", "message": "Synthesizing final response..."})

    synth_prompt = f"Original Request: {user_request}\n\n"
    for i, output in enumerate(worker_outputs):
        title = plan_json["tasks"][i]["title"]
        synth_prompt += f"--- Worker: {title} ---\n{output}\n\n"

    async for event, _, _ in run_agent_standard(
        synthesizer_agent, synth_prompt, "synthesis"
    ):
        if event.content and event.content.parts:
            part_text = event.content.parts[0].text
            if part_text:
                data = json.dumps({"type": "synthesis_step", "content": part_text})
                yield f"data: {data}\n\n"

    yield f"data: {json.dumps({'type': 'complete'})}\n\n"


@router.get("/stream_orchestrator")
async def stream_orchestrator(prompt: str) -> StreamingResponse:
    """Stream the orchestrator's execution."""
    return StreamingResponse(
        stream_orchestrator_generator(prompt), media_type="text/event-stream"
    )


def register(app: FastAPI) -> PatternMetadata:
    """Register the pattern."""
    return configure_pattern(
        app=app,
        router=router,
        config=PatternConfig(
            id="orchestrator",
            name="Orchestrator",
            description="Dynamically plans tasks and delegates them to parallel workers",
            icon="🎼",  # Musical score / Conductor icon
            base_file=__file__,
            handler=lambda _: {"message": "Use streaming"},
            template_name="orchestrator.html.j2",
        ),
    )
