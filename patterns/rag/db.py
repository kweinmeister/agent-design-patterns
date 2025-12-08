"""Database module for RAG pattern."""

import logging
import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import sqlite_vec

from patterns.rag import embeddings

logger = logging.getLogger(__name__)


def _get_db_path() -> str:
    """Determine the database path from env var or fallback to temp dir."""
    env_path = os.getenv("RAG_DB_PATH")
    if env_path:
        return env_path

    # Fallback to /tmp which is writable in Cloud Run
    return "/tmp/rag_demo.db"  # noqa: S108


DB_PATH = _get_db_path()
logger.info("RAG Database path set to: %s", DB_PATH)


class VecConnection(sqlite3.Connection):
    """SQLite connection that automatically loads sqlite-vec."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        """Initialize the connection and load the extension."""
        super().__init__(*args, **kwargs)
        self.enable_load_extension(True)  # noqa: FBT003
        sqlite_vec.load(self)
        self.enable_load_extension(False)  # noqa: FBT003

        # Enable WAL mode for concurrency
        self.execute("PRAGMA journal_mode=WAL;")
        self.execute("PRAGMA busy_timeout=5000;")
        self.execute("PRAGMA synchronous=NORMAL;")


@contextmanager
def get_db_connection(db_path: str) -> Iterator[sqlite3.Connection]:
    """Context manager for database connections.

    Creates a fresh connection per request to ensure thread safety.
    """
    conn = sqlite3.connect(db_path, factory=VecConnection, check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()


def init_db(db_path: str) -> None:
    """Initialize the SQLite database with the vector extension."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        # Create the documents table with a vector column
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT UNIQUE,
                embedding FLOAT[{embeddings.EMBEDDING_DIMENSIONS}]
            )
            """
        )
        conn.commit()


def add_documents(db_path: str, documents: list[tuple[str, list[float]]]) -> None:
    """Add documents and their embeddings to the database."""
    with get_db_connection(db_path) as conn:
        # Use executemany for bulk insertion
        data_to_insert = [
            (content, sqlite_vec.serialize_float32(embedding))
            for content, embedding in documents
        ]

        conn.executemany(
            "INSERT OR IGNORE INTO documents (content, embedding) VALUES (?, ?)",
            data_to_insert,
        )
        conn.commit()


def query_documents(
    db_path: str, query_embedding: list[float], limit: int = 5
) -> list[str]:
    """Query the database for similar documents using cosine distance."""
    if not Path(db_path).exists():
        return []

    query_blob = sqlite_vec.serialize_float32(query_embedding)

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT content, vec_distance_cosine(embedding, ?) as distance
            FROM documents
            ORDER BY distance
            LIMIT ?
            """,
            (query_blob, limit),
        )
        rows = cursor.fetchall()
        return [row[0] for row in rows]


def get_all_documents(db_path: str) -> list[str]:
    """Retrieve all documents from the database."""
    if not Path(db_path).exists():
        return []

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM documents")
        rows = cursor.fetchall()
        return [row[0] for row in rows]


def reset_db(db_path: str) -> None:
    """Reset the database by dropping the documents table."""
    if not Path(db_path).exists():
        return

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS documents")
        conn.commit()

    # Re-initialize to ensure table exists
    init_db(db_path)
