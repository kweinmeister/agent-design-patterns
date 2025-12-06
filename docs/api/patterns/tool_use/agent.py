"""Tool Use Agent Pattern."""

import ast
import operator
from typing import TYPE_CHECKING, Any

from google.adk.agents import LlmAgent

from patterns.config import GEMINI_MODEL

if TYPE_CHECKING:
    from collections.abc import Callable


def calculator(expression: str) -> str:
    """Evaluate a simple mathematical expression safely.

    Args:
        expression: The mathematical expression to evaluate.

    Returns:
        The result of the evaluation as a string.

    """
    # Safe operators mapping
    binary_operators: dict[type[ast.operator], Callable[[Any, Any], Any]] = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
    }

    def safe_eval(node: ast.AST) -> float | int:
        """Evaluate an AST node safely."""
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value

        if isinstance(node, ast.BinOp) and type(node.op) in binary_operators:
            return binary_operators[type(node.op)](
                safe_eval(node.left),
                safe_eval(node.right),
            )

        raise TypeError(node)

    try:
        return str(safe_eval(ast.parse(expression, mode="eval").body))
    except (SyntaxError, ValueError, TypeError) as e:
        return f"Error evaluating expression: {e}"


# --- Agent Definitions ---

# 1. Tool Use Agent
tool_use_agent = LlmAgent(
    name="ToolUseAgent",
    model=GEMINI_MODEL,
    instruction="""You are a helpful assistant with access to a calculator tool.
Use the calculator tool to answer mathematical questions.
If the user asks a question that requires calculation, use the tool.
Otherwise, answer directly.
""",
    tools=[calculator],
)

# 2. Pipeline
root_agent = tool_use_agent
