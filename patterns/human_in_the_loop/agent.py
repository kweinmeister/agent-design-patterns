"""Human-in-the-Loop Agent Pattern."""

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from patterns.config import GEMINI_MODEL


# --- Tool Definition ---
# --- Tool Definition ---
def publish_press_release(content: str) -> str:
    """Publish the press release to the global newswire.

    Args:
        content: The final text content to publish.

    Returns:
        A success message confirming publication.

    """
    # In a real app, this would hit an API.
    return f"{SUCCESS_MSG} Length: {len(content)} chars."


SUCCESS_MSG = "SUCCESS: Press release published to global wires."


def confirmation_criteria(content: dict[str, str]) -> bool:  # noqa: ARG001
    """Determine if a tool call requires human approval.

    This function acts as a filter for tool execution. In this specific pattern,
    we return `True` unconditionally because publishing a press release is
    always a sensitive action that requires review.

    Args:
        content: The argument payload that the agent intends to send to the tool.

    Returns:
        bool:
            - True: The tool call is SENSITIVE. The system will pause, present
              the `content` to the user, and wait for explicit approval.
            - False: The tool call is SAFE. It will execute automatically.

    """
    return True


# --- Agent Definition ---
hitl_agent = LlmAgent(
    name="GatekeeperAgent",
    model=GEMINI_MODEL,
    instruction="""You are a Corporate Communications Manager.
Your goal is to draft a professional press release based on the user's topic.
Once the user is satisfied with the draft, you should publish it using the
`publish_press_release` tool.
""",
    tools=[
        FunctionTool(publish_press_release, require_confirmation=confirmation_criteria)
    ],
)
