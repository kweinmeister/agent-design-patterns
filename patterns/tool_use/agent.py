"""Tool Use Agent Pattern."""

import ast
import operator
from typing import Any, cast

from google.adk.agents import LlmAgent

from patterns.config import GEMINI_MODEL

# --- Constants ---
MAX_EXPRESSION_LENGTH = 100

# Safe operators mapping
BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.FloorDiv: operator.floordiv,
}

UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def safe_eval(node: ast.AST) -> float | int:
    """Evaluate an AST node safely."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        msg = f"Unsupported type: {type(node.value)}"
        raise TypeError(msg)

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type in BINARY_OPERATORS:
            return BINARY_OPERATORS[cast("Any", op_type)](
                safe_eval(node.left), safe_eval(node.right)
            )

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type in UNARY_OPERATORS:
            return UNARY_OPERATORS[cast("Any", op_type)](safe_eval(node.operand))

    raise TypeError(node)


def calculator(expression: str) -> str:
    """Evaluate a simple mathematical expression safely.

    Args:
        expression: The mathematical expression to evaluate.

    Returns:
        The result of the evaluation as a string.

    """
    try:
        if len(expression) > MAX_EXPRESSION_LENGTH:
            return "Error: Expression too long"
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
