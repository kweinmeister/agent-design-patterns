"""Configuration for patterns."""

import os

# Default model to use for agents
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
