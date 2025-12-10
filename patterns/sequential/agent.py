"""Sequential Agent Pattern Logic."""

from google.adk.agents import LlmAgent, SequentialAgent

from patterns.config import GEMINI_MODEL

# --- Step 1: The Extractor ---
extractor_agent = LlmAgent(
    name="IncidentExtractor",
    model=GEMINI_MODEL,
    instruction="""You are a DevOps Log Analyst.
    Your task is to extract structured data from the provided raw log or user complaint.

    Extract the following fields into a JSON object:
    - timestamp (ISO 8601 format, or 'unknown')
    - error_code (e.g., 500, 404, or specific error string)
    - affected_service (the name of the system/module)
    - user_id (if present, else null)

    IMPORTANT: Output ONLY the raw JSON string. Do not use Markdown blocks (```json).
    """,
    output_key="structured_incident_data",
)

# --- Step 2: The Assessor ---
assessor_agent = LlmAgent(
    name="IncidentAssessor",
    model=GEMINI_MODEL,
    # We use 'include_contents="none"' to keep the context clean.
    # The agent only sees the specific data injected via the template below.
    include_contents="none",
    instruction="""You are an Incident Commander.
    Evaluate the severity of the incident based on the following data:

    DATA: {structured_incident_data}

    RUBRIC:
    - P1 (Critical): Affects 'PaymentService' OR 'AuthService'.
    - P2 (Major): Error code 500 but NOT critical services.
    - P3 (Minor): UI glitches, 404s, or single user issues.

    OUTPUT:
    Return ONLY the severity level (e.g., "P1", "P2", or "P3").
    """,
    output_key="severity_level",
)

# --- Step 3: The Communicator ---
communicator_agent = LlmAgent(
    name="IncidentCommunicator",
    model=GEMINI_MODEL,
    include_contents="none",
    instruction="""You are a Stakeholder Communications Manager.
    Draft an email regarding the incident.

    INCIDENT DETAILS: {structured_incident_data}
    SEVERITY: {severity_level}

    TONE GUIDELINES:
    - If P1: Urgent, apologetic, highly concise. Subject line must start with [URGENT].
    - If P2: Professional, informative.
    - If P3: Casual, "for your information" style.

    Format the output as a standard email with Subject and Body.
    """,
)

# --- The Pipeline ---
incident_triage_pipeline = SequentialAgent(
    name="IncidentTriagePipeline",
    sub_agents=[extractor_agent, assessor_agent, communicator_agent],
)
