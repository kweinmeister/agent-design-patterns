"""Reflection Agent Pattern."""

from typing import Any

from google.adk.agents import LlmAgent, LoopAgent, SequentialAgent
from google.adk.tools.tool_context import ToolContext

from patterns.config import GEMINI_MODEL

# --- Constants ---
STATE_CURRENT_DOC = "current_document"
STATE_CRITICISM = "criticism"
COMPLETION_PHRASE = "No major issues found."


# --- Tool Definition ---
def exit_loop(tool_context: ToolContext) -> dict[str, Any]:
    """Call this when the critique indicates no further changes are needed."""
    tool_context.actions.escalate = True
    return {}


# --- Agent Definitions ---

# 1. Initial Writer
initial_writer_agent = LlmAgent(
    name="InitialWriterAgent",
    model=GEMINI_MODEL,
    instruction="""You are a Creative Writing Assistant. Write the *first draft* of a
short story (2-4 sentences) based on the topic.
Topic: The user's message.
Output *only* the story text. Do not add introductions.""",
    output_key=STATE_CURRENT_DOC,
)

# 2a. Critic
critic_agent = LlmAgent(
    name="CriticAgent",
    model=GEMINI_MODEL,
    include_contents="none",
    instruction=f"""You are a Constructive Critic. Review the draft.
**Draft:**
```
{{current_document}}
```
**Task:**
IF improvements are needed: Provide 1-2 specific suggestions.
Output *only* the critique.
ELSE IF it is good: Respond *exactly* with "{COMPLETION_PHRASE}".
""",
    output_key=STATE_CRITICISM,
)

# 2b. Refiner
refiner_agent = LlmAgent(
    name="RefinerAgent",
    model=GEMINI_MODEL,
    include_contents="none",
    instruction=f"""You are a Refiner.
**Draft:**
```
{{current_document}}
```
**Critique:** {{criticism}}

**Task:**
IF critique is "{COMPLETION_PHRASE}":
        Output the draft text *exactly* as is, then Call 'exit_loop'.
ELSE: Improve the draft based on critique. Output *only* the refined text.
""",
    tools=[exit_loop],
    output_key=STATE_CURRENT_DOC,
)

# 3. Loop
refinement_loop = LoopAgent(
    name="RefinementLoop",
    sub_agents=[critic_agent, refiner_agent],
    max_iterations=5,
)

# 4. Pipeline
root_agent = SequentialAgent(
    name="ReflectionPipeline",
    sub_agents=[initial_writer_agent, refinement_loop],
)
