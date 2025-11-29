"""UI integration for the RAG pattern."""

from typing import Any

from fastapi import APIRouter, BackgroundTasks, FastAPI
from pydantic import BaseModel

from patterns.rag import db, ingest
from patterns.rag.agent import rag_agent
from patterns.utils import PatternUI

router = APIRouter()


class QueryRequest(BaseModel):
    """Request model for RAG query."""

    query: str


class RagUI(PatternUI):
    """UI integration for the RAG pattern."""

    def __init__(self) -> None:
        """Initialize the RagUI."""
        super().__init__(
            pattern_id="rag",
            name="RAG",
            description="Retrieves relevant information to ground responses",
            icon="📚",
            agent=rag_agent,
            current_file=__file__,
            template_name="rag.html.j2",
        )

    async def run_agent(self, user_request: str) -> dict[str, Any]:
        """Run the RAG agent and capture the output."""
        response_text = ""

        async for event, _runner, _session_id in self.run_agent_generator(user_request):
            if event.content and event.content.parts:
                text = event.content.parts[0].text
                if text:
                    response_text += text

        return {"final": response_text.strip()}


pattern_ui = RagUI()


def register(app: FastAPI) -> dict[str, str]:
    """Register the pattern with the main application.

    Returns metadata about the pattern.
    """
    # Ensure database connections are closed when the app shuts down
    app.add_event_handler("shutdown", db.close_connections)

    @app.post("/rag/ingest")
    async def ingest_knowledge(background_tasks: BackgroundTasks) -> dict[str, str]:
        """Trigger knowledge ingestion in the background."""
        background_tasks.add_task(ingest.ingest)
        return {"status": "Ingestion started"}

    @app.post("/rag/reset")
    def reset_knowledge() -> dict[str, str]:
        """Reset the knowledge base."""
        db.reset_db(db.DB_PATH)
        return {"status": "Knowledge base reset"}

    @app.get("/rag/knowledge")
    def get_knowledge() -> dict[str, list[str]]:
        """Get current knowledge base content."""
        documents = db.get_all_documents(db.DB_PATH)
        return {"documents": documents}

    @app.post("/rag/query")
    async def query_rag(request: QueryRequest) -> dict[str, str]:
        """Run the RAG agent."""
        return await pattern_ui.run_agent(request.query)

    return pattern_ui.register(app, copilotkit_path="/copilotkit/rag")
