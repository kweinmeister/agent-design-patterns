"""RAG Agent Pattern."""

from google.adk.agents import LlmAgent

from patterns.config import GEMINI_MODEL
from patterns.rag import db, embeddings


# --- Tool Definition ---
def retrieve_knowledge(query: str) -> str:
    """Retrieve relevant knowledge from the database for a given query."""
    query_embedding = embeddings.embed_query(query)
    results = db.query_documents(db.DB_PATH, query_embedding)
    return "\n\n".join(results)


# Define the RAG agent
rag_agent = LlmAgent(
    name="RagAgent",
    model=GEMINI_MODEL,
    instruction="""You are a helpful assistant with access to a knowledge base.
When answering user questions, ALWAYS use the `retrieve_knowledge` tool to find
relevant information. Base your answer primarily on the retrieved context.
If the retrieved information is not sufficient, acknowledge that you don't know
based on the available knowledge.
""",
    tools=[retrieve_knowledge],
)
