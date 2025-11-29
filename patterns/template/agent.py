"""Hello World Agent Pattern."""

from google.adk.agents import LlmAgent

from patterns.config import GEMINI_MODEL

# --- Agent Definition ---
root_agent = LlmAgent(
    name="HelloWorldAgent",
    model=GEMINI_MODEL,
    instruction="You are a helpful assistant. Reply to the user's message.",
)
