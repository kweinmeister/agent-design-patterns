"""Embeddings helper module using Gemini API."""

import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "768"))

# Initialize the client
client = genai.Client()


def _embed_content(text: str, task_type: str, title: str | None = None) -> list[float]:
    """Generate an embedding for a given text and task type."""
    config_args = {"task_type": task_type}
    if title:
        config_args["title"] = title

    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(**config_args),
    )
    if not result.embeddings or not result.embeddings[0].values:
        msg = f"Failed to generate embedding for task {task_type}"
        raise ValueError(msg)
    return result.embeddings[0].values


def embed_text(text: str) -> list[float]:
    """Generate an embedding for the given text using Gemini API."""
    return _embed_content(text, "RETRIEVAL_DOCUMENT", "Embedding of single text chunk")


def embed_query(text: str) -> list[float]:
    """Generate an embedding for a query text."""
    return _embed_content(text, "RETRIEVAL_QUERY")


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a batch of texts."""
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT", title="Embedding of text chunks"
        ),
    )
    if not result.embeddings:
        msg = "Failed to generate embeddings"
        raise ValueError(msg)
    embeddings = []
    for e in result.embeddings:
        if e.values is None:
            msg = "Missing embedding values in one or more results"
            raise ValueError(msg)
        embeddings.append(e.values)
    return embeddings
