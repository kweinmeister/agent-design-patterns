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
    (OUTPUT_DIR / "index.html").write_text(content + "\n", encoding="utf-8")

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
        json.dumps(static_patterns, indent=2) + "\n", encoding="utf-8"
    )

    logger.info("Processing %d patterns...", len(patterns_data))
    process_patterns(patterns_data, OUTPUT_DIR)


def process_patterns(patterns_data: list[dict], output_dir: Path) -> None:
    """Process patterns to generate raw files AND API JSON mocks."""
    # 1. Setup directories
    # Where raw files go (for README fetching)
    raw_root = output_dir / "api/patterns"
    raw_root.mkdir(parents=True, exist_ok=True)

    # Where code bundles go (for Code Viewer fetching)
    code_api_root = output_dir / "api/code"
    code_api_root.mkdir(parents=True, exist_ok=True)

    for pattern in patterns_data:
        p_id = pattern["id"]

        # Create raw file directory for this pattern
        p_raw_dir = raw_root / p_id
        p_raw_dir.mkdir(parents=True, exist_ok=True)

        src_dir = Path("patterns") / p_id
        if not src_dir.exists():
            continue

        # Dictionary to hold file contents for the JSON bundle
        code_files_bundle = {}

        for src_path in src_dir.iterdir():
            if not src_path.is_file():
                continue

            filename = src_path.name

            # Always copy README.md for the Info tab
            if filename == "README.md":
                shutil.copy2(src_path, p_raw_dir / filename)
                continue

            # Logic to select which files to expose in the code viewer
            # Matches PatternContext.get_code_files in utils.py
            is_code_file = (
                filename.endswith(".py")
                and not filename.startswith("test")
                and filename != "__init__.py"
            )

            if is_code_file:
                # 1. Read content
                content = src_path.read_text(encoding="utf-8")

                # 2. Add to JSON bundle
                code_files_bundle[filename] = content

                # 3. Copy raw file (optional, but good for consistency)
                shutil.copy2(src_path, p_raw_dir / filename)

        # 4. Write the mock API JSON response
        # This creates a file at docs/api/code/<pattern_id>
        # main.js fetches 'api/code/<id>' and parses it as JSON.
        (code_api_root / p_id).write_text(
            json.dumps(code_files_bundle), encoding="utf-8"
        )

    logger.info("Build complete!")


if __name__ == "__main__":
    build()
