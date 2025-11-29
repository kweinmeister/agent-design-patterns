"""Tests for the RAG Agent."""

import asyncio
from typing import Any
from unittest.mock import patch

import pytest
from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part

from patterns.rag.agent import rag_agent


@pytest.fixture
def mock_retrieval() -> Any:  # noqa: ANN401
    """Mock the retrieval dependencies."""
    with (
        patch("patterns.rag.db.query_documents") as mock_query_db,
        patch("patterns.rag.embeddings.embed_query") as mock_embed,
    ):
        # Mock embedding return
        mock_embed.return_value = [0.1] * 768
        # Mock DB return
        mock_query_db.return_value = [
            "Mission ID: M-009\nLog: Received a distress signal from the GSS Bagel. "
            "They are trapped in a cream cheese anomaly."
        ]
        yield mock_query_db


def test_rag_agent_end_to_end(mock_retrieval: Any) -> None:  # noqa: ANN401
    """Test the RAG agent end-to-end."""
    user_request = "What happened to the GSS Bagel?"

    app_name = "rag_app"
    runner = InMemoryRunner(agent=rag_agent, app_name=app_name)

    async def run_test() -> list[Any]:
        await runner.session_service.create_session(
            app_name=app_name,
            user_id="test_user",
            session_id="test_session",
        )

        return [
            event
            async for event in runner.run_async(
                user_id="test_user",
                session_id="test_session",
                new_message=Content(parts=[Part(text=user_request)]),
            )
        ]

    events = asyncio.run(run_test())

    assert events, "History should not be empty"

    # Check that we got a response from the model
    model_responses = [
        event for event in events if event.author == "RagAgent" and event.content
    ]
    assert model_responses, "Agent did not provide a response"

    # Verify the response contains information from the mocked retrieval
    last_event = model_responses[-1]
    assert last_event.content, "Event content should not be None"
    assert last_event.content.parts, "Content parts should not be empty"
    last_response = last_event.content.parts[0].text
    assert last_response, "Response text should not be None"
    response_lower = last_response.lower()
    assert "cream cheese" in response_lower or "bagel" in response_lower

    # Verify retrieval was called
    mock_retrieval.assert_called()
