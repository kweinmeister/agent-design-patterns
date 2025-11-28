"""UI integration for the Reflection pattern."""

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

from patterns.reflection.agent import STATE_CURRENT_DOC, root_agent

router = APIRouter()

# Setup templates and static files
current_dir = Path(__file__).parent.resolve()
templates_dir = current_dir / "templates"
static_dir = current_dir / "static"

templates = Jinja2Templates(directory=[templates_dir, Path("templates").resolve()])


async def run_reflection_agent(user_request: str) -> dict[str, Any]:
    """Run the reflection loop agent and capture the history."""
    history = []

    app_name = "reflection_app"
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

    # Get final state
    session = await runner.session_service.get_session(
        app_name=app_name,
        user_id="user",
        session_id=session_id,
    )

    final_doc = session.state.get(STATE_CURRENT_DOC, "") if session else ""

    return {"final": final_doc, "history": history}


sdk = CopilotKitRemoteEndpoint(
    actions=[
        Action(
            name="run_reflection_agent",
            description="Runs a reflection agent loop.",
            handler=run_reflection_agent,
        ),
    ],
)


def attach_reflection_ui(app: FastAPI, path: str = "/copilotkit/reflection") -> None:
    """Attach the reflection UI endpoint to the FastAPI app."""
    add_fastapi_endpoint(app, sdk, path)

    # Mount static files
    # Check if already mounted to avoid errors if called multiple times or conflicts
    # Using a unique name for this pattern's static files
    app.mount(
        "/reflection/static",
        StaticFiles(directory=static_dir),
        name="reflection_static",
    )

    @app.get("/demo/reflection", response_class=HTMLResponse)
    async def demo_reflection(request: Request, prompt: str = "") -> HTMLResponse:
        result = None
        if prompt:
            result = await run_reflection_agent(prompt)

        return templates.TemplateResponse(
            "reflection.html",
            {"request": request, "prompt": prompt, "result": result},
        )


def register(app: FastAPI) -> dict[str, str]:
    """Register the pattern with the main application.

    Returns metadata about the pattern.
    """
    attach_reflection_ui(app)
    return {
        "id": "reflection",
        "name": "Reflection",
        "description": "Critiques and refines its own output to improve quality",
        "icon": "🪞",
        "demo_url": "/demo/reflection",
    }
