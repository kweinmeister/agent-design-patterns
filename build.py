"""Build script for the static site."""

import json
import logging
import shutil
from pathlib import Path

from fastapi.testclient import TestClient

from main import app, load_patterns

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = TestClient(app)
OUTPUT_DIR = Path("docs")


def build() -> None:
    """Build the static site."""
    logger.info("Building static site to '%s'...", OUTPUT_DIR)

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    logger.info("Loading patterns...")
    load_patterns()

    logger.info("Copying static assets...")
    shutil.copytree("static", OUTPUT_DIR / "static")

    logger.info("Generating index.html...")
    response = client.get("/")
    response.raise_for_status()
    # Replace absolute URLs with relative ones for static hosting
    content = response.text.replace("http://testserver/", "./")
    (OUTPUT_DIR / "index.html").write_text(content + "\n")

    logger.info("Generating patterns.json...")
    patterns_resp = client.get("/patterns.json")
    patterns_resp.raise_for_status()
    patterns_data = patterns_resp.json()

    static_patterns = []
    for p in patterns_data:
        p_copy = p.copy()
        p_copy["demo_url"] = ""
        static_patterns.append(p_copy)

    (OUTPUT_DIR / "patterns.json").write_text(
        json.dumps(static_patterns, indent=2) + "\n"
    )

    api_root = OUTPUT_DIR / "api/patterns"
    logger.info("Processing %d patterns...", len(patterns_data))

    process_patterns(patterns_data, api_root)


def process_patterns(patterns_data: list[dict], api_root: Path) -> None:
    """Process and copy pattern files."""
    for pattern in patterns_data:
        p_id = pattern["id"]
        p_dir = api_root / p_id
        p_dir.mkdir(parents=True, exist_ok=True)

        src_dir = Path("patterns") / p_id
        if not src_dir.exists():
            continue

        for src_path in src_dir.iterdir():
            if not src_path.is_file():
                continue

            filename = src_path.name

            # Copy README.md and non-test Python files
            if filename == "README.md" or (
                filename.endswith(".py") and not filename.startswith("test")
            ):
                shutil.copy2(src_path, p_dir / filename)

    logger.info("Build complete!")


if __name__ == "__main__":
    build()
