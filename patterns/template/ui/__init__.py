"""UI integration for the Template pattern."""

from pathlib import Path

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part

from patterns.template.agent import root_agent

router = APIRouter()

# Setup templates
current_dir = Path(__file__).parent.resolve()
templates_dir = current_dir / "templates"

templates = Jinja2Templates(directory=[templates_dir, Path("templates").resolve()])


async def run_agent(user_request: str) -> str:
    """Run the agent."""
    app_name = "template_app"
    runner = InMemoryRunner(agent=root_agent, app_name=app_name)

    # Create session explicitly
    await runner.session_service.create_session(
        app_name=app_name,
        user_id="user",
        session_id="session",
    )

    response_text = ""
    async for event in runner.run_async(
        user_id="user",
        session_id="session",
        new_message=Content(parts=[Part(text=user_request)]),
    ):
        if event.content and event.content.parts:
            text = event.content.parts[0].text
            if text:
                response_text += text

    return response_text


def attach_ui(app: FastAPI) -> None:
    """Attach the UI endpoint."""

    @app.get("/demo/template", response_class=HTMLResponse)
    async def demo(request: Request, prompt: str = "") -> HTMLResponse:
        result = None
        if prompt:
            result = await run_agent(prompt)

        return templates.TemplateResponse(
            "pattern.html",
            {"request": request, "prompt": prompt, "result": result},
        )


def register(app: FastAPI) -> dict[str, str]:
    """Register the pattern."""
    attach_ui(app)
    return {
        "id": "template",
        "name": "Template Pattern",
        "description": "A template for creating new patterns.",
        "icon": "📝",
        "demo_url": "/demo/template",
    }
