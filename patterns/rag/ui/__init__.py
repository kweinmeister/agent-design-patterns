"""UI integration for the RAG pattern."""

from typing import Any

from fastapi import APIRouter, BackgroundTasks, FastAPI
from pydantic import BaseModel

from patterns.rag import db, ingest
from patterns.rag.agent import rag_agent
from patterns.utils import PatternMetadata, configure_pattern, run_agent_standard

router = APIRouter()


class QueryRequest(BaseModel):
    """Request model for RAG query."""

    query: str


async def run_rag_agent(user_request: str) -> dict[str, Any]:
    """Run the RAG agent and capture the output."""
    response_text = ""

    async for event, _runner, _session_id in run_agent_standard(
        rag_agent, user_request, "rag_app"
    ):
        if event.content and event.content.parts:
            text = event.content.parts[0].text
            if text:
                response_text += text

    return {"final": response_text.strip()}


def register(app: FastAPI) -> PatternMetadata:
    """Register the pattern with the main application.

    Returns metadata about the pattern.
    """
    # Ensure database connections are closed when the app shuts down
    app.add_event_handler("shutdown", db.close_connections)

    @router.post("/rag/ingest")
    async def ingest_knowledge(background_tasks: BackgroundTasks) -> dict[str, str]:
        """Trigger knowledge ingestion in the background."""
        background_tasks.add_task(ingest.ingest)
        return {"status": "Ingestion started"}

    @router.post("/rag/reset")
    def reset_knowledge() -> dict[str, str]:
        """Reset the knowledge base."""
        db.reset_db(db.DB_PATH)
        return {"status": "Knowledge base reset"}

    @router.get("/rag/knowledge")
    def get_knowledge() -> dict[str, list[str]]:
        """Get current knowledge base content."""
        documents = db.get_all_documents(db.DB_PATH)
        return {"documents": documents}

    @router.post("/rag/query")
    async def query_rag(request: QueryRequest) -> dict[str, str]:
        """Run the RAG agent."""
        return await run_rag_agent(request.query)

    return configure_pattern(
        app=app,
        router=router,
        pattern_id="rag",
        name="RAG",
        description="Retrieves relevant information to ground responses",
        icon="📚",
        base_file=__file__,
        handler=run_rag_agent,
        template_name="rag.html.j2",
        copilotkit_path="/copilotkit/rag",
    )
