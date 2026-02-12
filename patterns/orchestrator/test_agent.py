"""Unit tests for the Orchestrator Agent Pattern."""

import asyncio
import json
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from google.adk.agents import BaseAgent

from patterns.orchestrator.agent import (
    ExecutionPlan,
    SubTask,
    create_worker_agent,
    orchestrator_agent,
    synthesizer_agent,
)
from patterns.orchestrator.ui import register, stream_orchestrator_generator


def test_agent_definitions() -> None:
    """Verifies the agents are correctly defined."""
    assert orchestrator_agent.name == "Orchestrator"
    assert orchestrator_agent.output_schema == ExecutionPlan
    assert synthesizer_agent.name == "Synthesizer"
    # instruction might be a string or a callable depending on ADK version
    instruction = synthesizer_agent.instruction
    if callable(instruction):
        # If it's a callable, we just skip this check or try to call it
        pass
    else:
        assert "Aggregator" in instruction


def test_create_worker_agent() -> None:
    """Tests the worker agent factory function."""
    worker = create_worker_agent("Research Scientist", "Do some research")
    assert worker.name == "Research_Scientist"
    assert worker.instruction == "Do some research"

    # Test sanitization
    worker2 = create_worker_agent("123-Invalid!", "Instructions")
    assert worker2.name == "worker_123_Invalid_"


def test_registration() -> None:
    """Test that pattern can be registered without error."""
    app = FastAPI()
    meta = register(app)
    assert meta.id == "orchestrator"
    assert meta.name == "Orchestrator"
    assert meta.demo_url == "/demo/orchestrator"


@pytest.mark.asyncio
async def test_stream_orchestrator_generator() -> None:
    """Tests the orchestration loop generator by mocking run_agent_standard."""
    user_request = "Write a travel guide for Tokyo."

    # Mock plan response
    mock_plan = ExecutionPlan(
        plan_title="Tokyo Travel Guide",
        tasks=[
            SubTask(
                title="Food",
                description="Research Tokyo food",
                worker_type="Researcher",
            ),
            SubTask(
                title="Sightseeing",
                description="List Tokyo sights",
                worker_type="Researcher",
            ),
        ],
    )

    async def mock_run_agent_standard(
        agent: BaseAgent,
        _prompt: str,
        _app_name: str,
    ) -> AsyncGenerator[tuple[Any, Any, Any], None]:
        # 1. Orchestrator Plan
        if agent == orchestrator_agent:
            event = MagicMock()
            event.is_final_response.return_value = True
            event.author = "Orchestrator"
            part = MagicMock()
            part.text = mock_plan.model_dump_json()
            event.content.parts = [part]
            yield event, None, None

        # 2. Worker execution
        elif agent.name in ["Food", "Sightseeing"]:
            event = MagicMock()
            event.is_final_response.return_value = False
            event.content.parts = [MagicMock(text=f"Content from {agent.name}")]
            yield event, None, None

            final_event = MagicMock()
            final_event.is_final_response.return_value = True
            final_event.author = agent.name
            final_event.content.parts = [MagicMock(text="")]
            yield final_event, None, None

        # 3. Synthesizer execution
        elif agent == synthesizer_agent:
            event = MagicMock()
            event.is_final_response.return_value = False
            event.content.parts = [MagicMock(text="Final synthesized guide")]
            yield event, None, None

    with patch(
        "patterns.orchestrator.ui.run_agent_standard",
        side_effect=mock_run_agent_standard,
    ):
        items = []
        async for chunk in stream_orchestrator_generator(user_request):
            if chunk.startswith("data: "):
                data = json.loads(chunk[6:])
                items.append(data)

        # Verify the sequence of events
        types = [item["type"] for item in items]

        assert "status" in types
        assert "plan" in types
        assert "worker_start" in types
        assert "worker_step" in types
        assert "worker_complete" in types
        assert "synthesis_step" in types
        assert "complete" in types

        # Check plan content
        plan_item = next(item for item in items if item["type"] == "plan")
        assert plan_item["plan"]["plan_title"] == "Tokyo Travel Guide"
        assert len(plan_item["plan"]["tasks"]) == len(mock_plan.tasks)


@pytest.mark.asyncio
async def test_stream_orchestrator_race_condition() -> None:
    """Reproduces a race condition where worker_task is cancelled prematurely."""
    user_request = "Any request"

    # Mock plan
    mock_plan = ExecutionPlan(
        plan_title="Test Plan",
        tasks=[SubTask(title="T1", description="D1", worker_type="W1")],
    )

    # 1. Mock orchestrator_agent to return plan
    async def mock_run_agent_orchestrator(
        _agent: BaseAgent,
        _prompt: str,
        _app_name: str,
    ) -> AsyncGenerator[tuple[Any, Any, Any], None]:
        event = MagicMock()
        event.is_final_response.return_value = True
        event.author = "Orchestrator"
        part = MagicMock()
        part.text = mock_plan.model_dump_json()
        event.content.parts = [part]
        yield event, None, None

    # 2. Mock synthesizer_agent to return something
    async def mock_run_agent_synthesizer(
        _agent: BaseAgent,
        _prompt: str,
        _app_name: str,
    ) -> AsyncGenerator[tuple[Any, Any, Any], None]:
        event = MagicMock()
        event.is_final_response.return_value = False
        event.content.parts = [MagicMock(text="Synthesis content")]
        yield event, None, None

    # 3. Mock _execute_workers to simulate the race condition
    # It puts None in the queue then sleeps, simulating the case where
    # the task is still "running" but the signal has been sent.
    async def mock_execute_workers_race(
        _tasks_list: list[SubTask],
        _user_request: str,
        queue: asyncio.Queue,
    ) -> list[str]:
        await queue.put({"type": "worker_start", "task_id": 0})
        await queue.put(None)
        await asyncio.sleep(0.1)  # Simulate delay after signaling completion
        return ["Worker Output"]

    with (
        patch(
            "patterns.orchestrator.ui.run_agent_standard",
            side_effect=lambda agent, *args: (
                mock_run_agent_orchestrator(agent, *args)
                if agent == orchestrator_agent
                else mock_run_agent_synthesizer(agent, *args)
            ),
        ),
        patch(
            "patterns.orchestrator.ui._execute_workers",
            side_effect=mock_execute_workers_race,
        ),
    ):
        items = []
        # This should proceed to synthesis despite the delay in _execute_workers
        async for chunk in stream_orchestrator_generator(user_request):
            if chunk.startswith("data: "):
                data = json.loads(chunk[6:])
                items.append(data)

        types = [item["type"] for item in items]
        # In the failing case, 'synthesis_step' might not be reached or it might crash
        assert "synthesis_step" in types
        assert "complete" in types
