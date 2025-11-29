"""Ingestion module for RAG pattern."""

import csv
import logging
from pathlib import Path

from patterns.rag import db, embeddings

logger = logging.getLogger(__name__)


def load_knowledge(file_path: str, *, skip_header: bool = True) -> list[str]:
    """Load and split the knowledge base CSV file."""
    chunks = []
    with Path(file_path).open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        if skip_header:
            next(reader, None)
        for row in reader:
            if row:
                # Combine all fields into a single text chunk
                chunk = "\n".join(row)
                chunks.append(chunk)
    return chunks


def ingest() -> None:
    """Ingest knowledge into the target database."""
    knowledge_file = "patterns/rag/data/knowledge.csv"
    if not Path(knowledge_file).exists():
        return

    db_path = db.DB_PATH

    # Initialize database
    db.init_db(db_path)

    # Load and embed documents
    chunks = load_knowledge(knowledge_file)
    documents = []
    if chunks:
        embeddings_list = embeddings.embed_texts(chunks)
        documents = list(zip(chunks, embeddings_list, strict=True))

    # Add to database
    db.add_documents(db_path, documents)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ingest()
