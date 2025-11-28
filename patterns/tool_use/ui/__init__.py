"""UI integration for the Tool Use pattern."""

import uuid
from pathlib import Path
from typing import Any

from copilotkit import Action, CopilotKitRemoteEndpoint
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part

from patterns.tool_use.agent import root_agent

router = APIRouter()

# Setup templates and static files
current_dir = Path(__file__).parent.resolve()
templates_dir = current_dir / "templates"
static_dir = current_dir / "static"

templates = Jinja2Templates(directory=[templates_dir, Path("templates").resolve()])


async def run_tool_use_agent(user_request: str) -> dict[str, Any]:
    """Run the tool use agent and capture the history."""
    history = []

    app_name = "tool_use_app"
    runner = InMemoryRunner(agent=root_agent, app_name=app_name)

    # Create session explicitly
    session_id = str(uuid.uuid4())
    await runner.session_service.create_session(
        app_name=app_name,
        user_id="user",
        session_id=session_id,
    )

    # Run agent and capture events
    async for event in runner.run_async(
        user_id="user",
        session_id=session_id,
        new_message=Content(parts=[Part(text=user_request)]),
    ):
        if event.content and event.content.parts:
            text = event.content.parts[0].text
            if text:
                history.append({"role": event.author, "content": text})

    return {"history": history}


sdk = CopilotKitRemoteEndpoint(
    actions=[
        Action(
            name="run_tool_use_agent",
            description="Runs a tool use agent.",
            handler=run_tool_use_agent,
        ),
    ],
)


def attach_tool_use_ui(app: FastAPI, path: str = "/copilotkit/tool_use") -> None:
    """Attach the tool use UI endpoint to the FastAPI app."""
    add_fastapi_endpoint(app, sdk, path)

    # Mount static files
    app.mount(
        "/tool_use/static",
        StaticFiles(directory=static_dir),
        name="tool_use_static",
    )

    @app.get("/demo/tool_use", response_class=HTMLResponse)
    async def demo_tool_use(request: Request, prompt: str = "") -> HTMLResponse:
        result = None
        if prompt:
            result = await run_tool_use_agent(prompt)

        return templates.TemplateResponse(
            "tool_use.html",
            {"request": request, "prompt": prompt, "result": result},
        )


def register(app: FastAPI) -> dict[str, str]:
    """Register the pattern with the main application.

    Returns metadata about the pattern.
    """
    attach_tool_use_ui(app)
    return {
        "id": "tool_use",
        "name": "Tool Use",
        "description": "Uses external tools to perform tasks",
        "icon": "🛠️",
        "demo_url": "/demo/tool_use",
    }
