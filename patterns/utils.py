"""Shared UI utilities for patterns."""

import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from pathlib import Path
from typing import Any

from copilotkit import Action, CopilotKitRemoteEndpoint
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from google.adk.agents import BaseAgent
from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part
from pydantic import BaseModel


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
            ]
        )
        self.template_name = template_name

    def get_code_files(self) -> dict[str, str]:
        """Get code files for the pattern."""
        files = {}
        for item in self.pattern_dir.glob("*.py"):
            if item.name == "__init__.py" or item.name.startswith("test_"):
                continue
            files[item.name] = item.read_text()

        # Sort by filename
        return dict(sorted(files.items()))


async def run_agent_standard(
    agent: BaseAgent,
    user_request: str,
    app_name: str,
) -> AsyncGenerator[tuple[Any, InMemoryRunner, str]]:
    """Handle runner setup and event loop.

    Yields (event, runner, session_id).
    """
    runner = InMemoryRunner(agent=agent, app_name=app_name)
    session_id = str(uuid.uuid4())

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


class PatternMetadata(BaseModel):
    """Metadata for a pattern."""

    id: str
    name: str
    description: str
    icon: str
    demo_url: str


def configure_pattern(  # noqa: PLR0913
    app: FastAPI,
    router: APIRouter,
    pattern_id: str,
    name: str,
    description: str,
    icon: str,
    base_file: str,
    handler: Callable[[str], Awaitable[Any]],
    template_name: str,
    copilotkit_path: str | None = None,
) -> PatternMetadata:
    """Configure a pattern with standard routes and integration.

    Args:
        app: The main FastAPI app.
        router: The pattern's APIRouter.
        pattern_id: The pattern ID.
        name: The pattern name.
        description: The pattern description.
        icon: The pattern icon.
        base_file: The __file__ of the calling module.
        handler: The async function to run the agent.
        template_name: The name of the Jinja2 template.
        copilotkit_path: Optional path for CopilotKit integration.

    Returns:
        Metadata object for the pattern.

    """
    ctx = PatternContext(base_file, template_name)
    static_dir = ctx.base_path / "static"

    # Mount static files if directory exists
    # Note: We mount on the main app because router mounts are relative
    # and can be tricky with static assets in templates.
    if static_dir.exists():
        app.mount(
            f"/{pattern_id}/static",
            StaticFiles(directory=static_dir),
            name=f"{pattern_id}_static",
        )

    # API: Get Code
    @router.get(f"/api/code/{pattern_id}")
    def get_code() -> dict[str, str]:
        return ctx.get_code_files()

    # API: Demo Page
    @router.get(f"/demo/{pattern_id}", response_class=HTMLResponse)
    async def demo(request: Request, prompt: str = "") -> HTMLResponse:
        result = None
        if prompt:
            result = await handler(prompt)

        return ctx.templates.TemplateResponse(
            ctx.template_name,
            {
                "request": request,
                "prompt": prompt,
                "result": result,
                "code_files": ctx.get_code_files(),
                "pattern": PatternMetadata(
                    id=pattern_id,
                    name=name,
                    description=description,
                    icon=icon,
                    demo_url=f"/demo/{pattern_id}",
                ),
            },
        )

    # CopilotKit integration
    if copilotkit_path:
        sdk = CopilotKitRemoteEndpoint(
            actions=[
                Action(
                    name=f"run_{pattern_id}_agent",
                    description=f"Runs a {name} agent.",
                    handler=handler,
                ),
            ],
        )
        add_fastapi_endpoint(app, sdk, copilotkit_path)

    # Include the router in the main app
    app.include_router(router)

    return PatternMetadata(
        id=pattern_id,
        name=name,
        description=description,
        icon=icon,
        demo_url=f"/demo/{pattern_id}",
    )
