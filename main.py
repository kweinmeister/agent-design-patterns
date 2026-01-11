"""Main application entry point."""

import importlib
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from patterns.utils import PatternMetadata

load_dotenv()

# Registry for patterns
patterns: list[PatternMetadata] = []
logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="templates")


def load_patterns() -> None:
    """Dynamically load patterns from the patterns directory."""
    patterns.clear()
    patterns_dir = Path(__file__).parent / "patterns"

    # Ensure patterns directory exists
    if not patterns_dir.exists():
        return

    # Iterate over subdirectories in patterns
    for item in patterns_dir.iterdir():
        if item.is_dir():
            # Skip template directory
            if item.name == "template":
                continue

            # Check for ui.py or ui package
            ui_path = item / "ui.py"
            ui_package_path = item / "ui"

            if ui_path.exists() or (
                ui_package_path.is_dir() and (ui_package_path / "__init__.py").exists()
            ):
                try:
                    # Import the module
                    module_name = f"patterns.{item.name}.ui"
                    module = importlib.import_module(module_name)

                    # Check for register function
                    if hasattr(module, "register"):
                        metadata = module.register(app)
                        patterns.append(metadata)
                except (ImportError, AttributeError):
                    logger.exception("Error loading pattern %s", item.name)

    # Sort patterns alphabetically by name
    patterns.sort(key=lambda x: x.name)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """Load patterns on startup."""
    load_patterns()
    yield


app = FastAPI(lifespan=lifespan)

# Ensure we trust the proxy headers (required for Cloud Run to handle HTTPS correctly)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")  # type: ignore[arg-type]

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
# Mount patterns directory to serve raw files
app.mount("/api/patterns", StaticFiles(directory="patterns"), name="patterns")


@app.get("/patterns.json")
def get_patterns() -> list[PatternMetadata]:
    """Return the list of available patterns."""
    return patterns


@app.get("/")
def read_root(request: Request) -> Response:
    """Serve the static index.html."""
    return templates.TemplateResponse("index.html.j2", {"request": request})


def main() -> None:
    """Run the application."""
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)  # noqa: S104


if __name__ == "__main__":
    main()
