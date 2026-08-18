"""Configuration for patterns."""

import os

# Default model to use for agents
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")
