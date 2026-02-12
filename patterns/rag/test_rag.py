"""Tests for the RAG pattern components."""

import sqlite3
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from patterns.rag import agent, db, ingest


# Mock embeddings to avoid API calls during tests
@pytest.fixture
def mock_embeddings() -> Any:  # noqa: ANN401
    """Mock the embeddings module."""
    with (
        patch("patterns.rag.embeddings.embed_text") as mock_text,
        patch("patterns.rag.embeddings.embed_query") as mock_query,
    ):
        mock_text.return_value = [0.1] * 768
        mock_query.return_value = [0.1] * 768
        yield mock_text


@pytest.fixture
def temp_db(tmp_path: Path) -> str:
    """Create a temporary database path."""
    db_path = tmp_path / "test.db"
    return str(db_path)


def test_db_init(temp_db: str) -> None:
    """Test database initialization."""
    db.init_db(temp_db)
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Check if table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='documents'",
    )
    assert cursor.fetchone() is not None
    conn.close()


@pytest.mark.usefixtures("mock_embeddings")
def test_add_and_query_documents(
    temp_db: str,
) -> None:
    """Test adding and querying documents."""
    db.init_db(temp_db)

    documents = [("This is a test document.", [0.1] * 768)]
    db.add_documents(temp_db, documents)

    # Query
    results = db.query_documents(temp_db, [0.1] * 768)
    assert len(results) > 0
    assert results[0] == "This is a test document."


@pytest.mark.usefixtures("mock_embeddings")
def test_ingest(
    temp_db: str,
    tmp_path: Path,
) -> None:
    """Test ingestion process."""
    # Create a dummy knowledge file
    data_dir = tmp_path / "patterns/rag/data"
    data_dir.mkdir(parents=True)
    knowledge_file = data_dir / "knowledge.csv"
    knowledge_file.write_text("mission_id,log_entry\nM-001,Test Log")

    with (
        patch("patterns.rag.ingest.db.DB_PATH", temp_db),
        patch("patterns.rag.ingest.load_knowledge") as mock_load,
    ):
        mock_load.return_value = ["Mission ID: M-001\nLog: Test Log"]

        ingest.ingest()

        # Verify data in DB
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM documents")
        count = cursor.fetchone()[0]
        assert count == 1
        conn.close()


@pytest.mark.usefixtures("mock_embeddings")
def test_agent_tool() -> None:
    """Test the agent's retrieval tool."""
    # Mock db.query_documents to return a result
    with patch("patterns.rag.db.query_documents") as mock_query_db:
        mock_query_db.return_value = ["Retrieved content"]

        result = agent.retrieve_knowledge("test query")
        assert "Retrieved content" in result
        mock_query_db.assert_called_once()
