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
ALLOWLIST = ["agent.py", "README.md", "__init__.py"]


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
    (OUTPUT_DIR / "index.html").write_bytes(response.content)

    logger.info("Generating patterns.json...")
    patterns_resp = client.get("/patterns.json")
    patterns_resp.raise_for_status()
    patterns_data = patterns_resp.json()

    static_patterns = []
    for p in patterns_data:
        p_copy = p.copy()
        p_copy["demo_url"] = ""
        static_patterns.append(p_copy)

    (OUTPUT_DIR / "patterns.json").write_text(json.dumps(static_patterns, indent=2))

    api_root = OUTPUT_DIR / "api/patterns"
    logger.info("Processing %d patterns...", len(patterns_data))

    for pattern in patterns_data:
        p_id = pattern["id"]
        p_dir = api_root / p_id
        p_dir.mkdir(parents=True, exist_ok=True)

        for filename in ALLOWLIST:
            src_path = Path("patterns") / p_id / filename
            dest_path = p_dir / filename

            if src_path.exists():
                shutil.copy2(src_path, dest_path)

    logger.info("Build complete!")


if __name__ == "__main__":
    build()
