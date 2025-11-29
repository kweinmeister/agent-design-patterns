"""Shared UI utilities for patterns."""

import uuid
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from copilotkit import Action, CopilotKitRemoteEndpoint
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part


class PatternUI(ABC):
    """Abstract base class for pattern UI integration."""

    def __init__(  # noqa: PLR0913
        self,
        pattern_id: str,
        name: str,
        description: str,
        icon: str,
        agent: Agent,
        current_file: str,
        template_name: str | None = None,
    ) -> None:
        """Initialize the PatternUI helper."""
        self.pattern_id = pattern_id
        self.name = name
        self.description = description
        self.icon = icon
        self.agent = agent

        current_dir = Path(current_file).parent.resolve()
        self.templates_dir = current_dir / "templates"
        self.static_dir = current_dir / "static"

        self.templates = Jinja2Templates(
            directory=[self.templates_dir, Path("templates").resolve()]
        )
        self.app_name = f"{pattern_id}_app"
        self.template_name = template_name or f"{pattern_id}.html"

    async def run_agent_generator(
        self, user_request: str
    ) -> AsyncGenerator[tuple[Any, InMemoryRunner, str], None]:
        """Run the agent and yield events, runner, and session_id."""
        runner = InMemoryRunner(agent=self.agent, app_name=self.app_name)
        session_id = str(uuid.uuid4())

        await runner.session_service.create_session(
            app_name=self.app_name,
            user_id="user",
            session_id=session_id,
        )

        async for event in runner.run_async(
            user_id="user",
            session_id=session_id,
            new_message=Content(parts=[Part(text=user_request)]),
        ):
            yield event, runner, session_id

    @abstractmethod
    async def run_agent(self, user_request: str) -> Any:  # noqa: ANN401
        """Run the agent and return the result."""

    def attach(
        self,
        app: FastAPI,
        copilotkit_path: str | None = None,
    ) -> None:
        """Attach the pattern UI to the FastAPI app."""
        # Mount static files if directory exists
        if self.static_dir.exists():
            app.mount(
                f"/{self.pattern_id}/static",
                StaticFiles(directory=self.static_dir),
                name=f"{self.pattern_id}_static",
            )

        # CopilotKit integration
        if copilotkit_path:
            sdk = CopilotKitRemoteEndpoint(
                actions=[
                    Action(
                        name=f"run_{self.pattern_id}_agent",
                        description=f"Runs a {self.name} agent.",
                        handler=self.run_agent,
                    ),
                ],
            )
            add_fastapi_endpoint(app, sdk, copilotkit_path)

        # Demo route
        @app.get(f"/demo/{self.pattern_id}", response_class=HTMLResponse)
        async def demo(request: Request, prompt: str = "") -> HTMLResponse:
            result = None
            if prompt:
                result = await self.run_agent(prompt)

            return self.templates.TemplateResponse(
                self.template_name,
                {"request": request, "prompt": prompt, "result": result},
            )

    def register(
        self,
        app: FastAPI,
        copilotkit_path: str | None = None,
    ) -> dict[str, str]:
        """Register the pattern and return metadata."""
        self.attach(app, copilotkit_path)
        return {
            "id": self.pattern_id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "demo_url": f"/demo/{self.pattern_id}",
        }
