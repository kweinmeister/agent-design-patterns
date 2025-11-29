"""Embeddings helper module using Gemini API."""

import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "768"))

# Initialize the client
client = genai.Client()


def embed_text(text: str) -> list[float]:
    """Generate an embedding for the given text using Gemini API."""
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT", title="Embedding of single text chunk"
        ),
    )
    if not result.embeddings or not result.embeddings[0].values:
        msg = "Failed to generate embedding"
        raise ValueError(msg)
    return result.embeddings[0].values


def embed_query(text: str) -> list[float]:
    """Generate an embedding for a query text."""
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
    )
    if not result.embeddings or not result.embeddings[0].values:
        msg = "Failed to generate embedding"
        raise ValueError(msg)
    return result.embeddings[0].values
