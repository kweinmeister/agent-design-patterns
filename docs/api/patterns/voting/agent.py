"""Voting / Best-of-N Agent Pattern."""

from google.adk.agents import LlmAgent

from patterns.config import GEMINI_MODEL

# --- Generator Agents ---
# We define three distinct agents to produce diverse outputs based on different
# personas.

humorous_agent = LlmAgent(
    name="HumorousAgent",
    model=GEMINI_MODEL,
    instruction="""You are a marketing copywriter with a witty, humorous style.
Your task is to write a short, catchy ad copy for the product described by the user.
Keep it under 50 words. Be funny and memorable.""",
)

professional_agent = LlmAgent(
    name="ProfessionalAgent",
    model=GEMINI_MODEL,
    instruction="""You are a marketing copywriter with a professional, trustworthy,
and elegant style. Your task is to write a short, catchy ad copy for the product
described by the user. Keep it under 50 words. Focus on value, reliability, and
trust.""",
)

urgent_agent = LlmAgent(
    name="UrgentAgent",
    model=GEMINI_MODEL,
    instruction="""You are a marketing copywriter who uses urgency and excitement
(FOMO). Your task is to write a short, catchy ad copy for the product described by
the user. Keep it under 50 words. Use strong calls to action and time-sensitive
language.""",
)

# --- The Judge Agent ---
# This agent evaluates the options and picks the winner.

judge_agent = LlmAgent(
    name="JudgeAgent",
    model=GEMINI_MODEL,
    instruction="""You are a Senior Editor. You will receive multiple ad copy options
for a product.
Evaluate them based on clarity, catchiness, and persuasion.

Task:
1. Briefly analyze each option.
2. Select the single best one.

Output Format:
**Winner:** [Style Name]
**Reason:** [Brief explanation]
**Final Polish:** [The text of the winning copy, potentially slightly improved]
""",
)
