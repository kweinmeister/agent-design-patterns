"""Shared UI utilities for patterns."""

import json
import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from pathlib import Path
from typing import Any

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from google.adk.agents import BaseAgent
from google.adk.runners import InMemoryRunner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai.types import Content, Part
from pydantic import BaseModel, ConfigDict

# Create a global service singleton
_GLOBAL_SESSION_SERVICE = InMemorySessionService()


# Threshold for including __init__.py files in code viewer
_INIT_FILE_SIZE_THRESHOLD = 100


class PatternContext:
    """Helper to manage file paths and templating."""

    def __init__(self, base_file: str, template_name: str) -> None:
        """Initialize the PatternContext."""
        self.base_path = Path(base_file).parent.resolve()
        self.pattern_dir = self.base_path.parent
        self.templates = Jinja2Templates(
            directory=[
                self.base_path / "templates",
                Path("templates").resolve(),
            ],
        )
        self.template_name = template_name

    def _should_include(self, item: Path) -> bool:
        """Check if a Python file should be included in the code viewer."""
        if item.name.startswith("test_"):
            return False
        if item.name == "__init__.py":
            return item.stat().st_size > _INIT_FILE_SIZE_THRESHOLD
        return True

    def get_code_files(self) -> dict[str, str]:
        """Get code files for the pattern."""
        files = {}

        def _scan_dir(directory: Path, prefix: str = "") -> None:
            if not directory.is_dir():
                return
            for item in directory.glob("*.py"):
                if self._should_include(item):
                    files[f"{prefix}{item.name}"] = item.read_text()

        _scan_dir(self.pattern_dir)
        _scan_dir(self.pattern_dir / "ui", "ui/")

        # Sort by filename
        return dict(sorted(files.items()))


def parse_json_from_text(text: str) -> dict[str, Any] | list[Any] | None:
    """Robustly parse JSON from text, handling Markdown code blocks.

    Args:
        text: The string containing potential JSON.

    Returns:
        Parsed JSON object/list, or None if parsing fails.

    """
    if not text:
        return None

    # Strip Markdown code blocks
    clean_text = text.strip()
    if clean_text.startswith("```"):
        try:
            # Remove first line (```json or ```)
            clean_text = clean_text.split("\n", 1)[1]
            # Remove last line (```)
            if clean_text.endswith("```"):
                clean_text = clean_text.rsplit("\n", 1)[0]
        except IndexError:
            return None

    clean_text = clean_text.strip()

    try:
        return json.loads(clean_text)
    except json.JSONDecodeError:
        return None


async def run_agent_standard(
    agent: BaseAgent,
    user_request: str,
    app_name: str,
    session_id: str | None = None,
) -> AsyncGenerator[tuple[Any, InMemoryRunner, str]]:
    """Handle runner setup and event loop.

    Yields (event, runner, session_id).
    """
    # Use provided session_id (from frontend) or generate one (for stateless demos)
    if not session_id:
        session_id = str(uuid.uuid4())

    # Pass the global service to the runner
    runner = InMemoryRunner(
        agent=agent,
        app_name=app_name,
    )
    # Overwrite the session service with the global one to persist state
    runner.session_service = _GLOBAL_SESSION_SERVICE

    # Ensure the session exists in the global store
    if not await runner.session_service.get_session(
        app_name=app_name,
        user_id="user",
        session_id=session_id,
    ):
        await runner.session_service.create_session(
            app_name=app_name,
            user_id="user",
            session_id=session_id,
        )

    async for event in runner.run_async(
        user_id="user",
        session_id=session_id,
        new_message=Content(parts=[Part(text=user_request)]),
    ):
        yield event, runner, session_id


async def stream_agent_events(
    agent: BaseAgent,
    user_request: str,
    app_name: str,
    session_id: str | None = None,
) -> AsyncGenerator[str, None]:
    """Yield SSE events from ADK agents."""
    final_text = ""

    # Reuse run_agent_standard to ensure state persistence
    async for event, _, _ in run_agent_standard(
        agent,
        user_request,
        app_name,
        session_id,
    ):
        if event.content and event.content.parts:
            text = event.content.parts[0].text
            if text:
                final_text += text
                # Standard step event
                data = json.dumps(
                    {"type": "step", "role": event.author, "content": text},
                )
                yield f"data: {data}\n\n"

    # Standard complete event
    yield f"data: {json.dumps({'type': 'complete', 'final': final_text})}\n\n"


async def run_and_collect_history(
    agent: BaseAgent,
    user_request: str,
    app_name: str,
) -> list[dict[str, str]]:
    """Run an agent and collect its history.

    Args:
        agent: The agent to run.
        user_request: The user's input prompt.
        app_name: The application name for the session.

    Returns:
        A list of messages (history) from the agent run.

    """
    history = []
    async for event, _, _ in run_agent_standard(agent, user_request, app_name):
        if event.content and event.content.parts:
            text = event.content.parts[0].text
            if text:
                history.append({"role": event.author, "content": text})
    return history


class PatternMetadata(BaseModel):
    """Metadata for a pattern."""

    id: str
    name: str
    description: str
    icon: str
    demo_url: str


class PatternConfig(BaseModel):
    """Configuration for a pattern."""

    id: str
    name: str
    description: str
    icon: str
    base_file: str
    handler: Callable[[str], Awaitable[Any]] | None
    template_name: str

    model_config = ConfigDict(arbitrary_types_allowed=True)


def configure_pattern(
    app: FastAPI,
    router: APIRouter,
    config: PatternConfig,
    agent: BaseAgent | None = None,
) -> PatternMetadata:
    """Configure a pattern with standard routes and integration.

    Args:
        app: The main FastAPI app.
        router: The pattern's APIRouter.
        config: The pattern configuration.
        agent: Optional agent instance to auto-generate handler.

    Returns:
        Metadata object for the pattern.

    """
    # Auto-generate handler if agent is provided but handler is not
    if agent and not config.handler:

        async def default_handler(prompt: str) -> dict[str, Any]:
            if not agent:
                msg = "Agent is required for default handler"
                raise ValueError(msg)
            # Uses the standard history collector
            history = await run_and_collect_history(agent, prompt, config.id)
            return {
                "history": history,
                "result": history[-1]["content"] if history else "",
            }

        config.handler = default_handler

    if not config.handler:
        # Fallback to avoid runtime errors if no handler is set
        async def noop_handler(_prompt: str) -> dict[str, Any]:
            return {}

        config.handler = noop_handler

    ctx = PatternContext(config.base_file, config.template_name)
    static_dir = ctx.base_path / "static"

    # Mount static files if directory exists
    # Note: We mount on the main app because router mounts are relative
    # and can be tricky with static assets in templates.
    if static_dir.exists():
        app.mount(
            f"/{config.id}/static",
            StaticFiles(directory=static_dir),
            name=f"{config.id}_static",
        )

    # API: Get Code
    @router.get(f"/api/code/{config.id}")
    def get_code() -> dict[str, str]:
        return ctx.get_code_files()

    # API: Demo Page
    @router.get(f"/demo/{config.id}", response_class=HTMLResponse)
    async def demo(request: Request, prompt: str = "") -> HTMLResponse:
        result = None
        if prompt and config.handler:
            result = await config.handler(prompt)

        return ctx.templates.TemplateResponse(
            ctx.template_name,
            {
                "request": request,
                "prompt": prompt,
                "result": result,
                "code_files": ctx.get_code_files(),
                "pattern": PatternMetadata(
                    id=config.id,
                    name=config.name,
                    description=config.description,
                    icon=config.icon,
                    demo_url=f"/demo/{config.id}",
                ),
            },
        )

    # Include the router in the main app
    app.include_router(router)

    return PatternMetadata(
        id=config.id,
        name=config.name,
        description=config.description,
        icon=config.icon,
        demo_url=f"/demo/{config.id}",
    )
