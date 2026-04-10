from unittest.mock import MagicMock

import pytest
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai.types import Content, Part

from agents.orchestrator.agent import StateCapturer


@pytest.mark.asyncio
async def test_state_capturer_streaming():
    """Test that StateCapturer accumulates text from multiple streaming events from the same author."""
    # Create the agent
    capturer = StateCapturer(output_key="findings")

    # Mock context
    ctx = MagicMock(spec=InvocationContext)
    ctx.session = MagicMock()
    ctx.session.state = {}

    # Create a history of events
    # Event 1: Researcher chunk 1
    # Event 2: Researcher chunk 2
    # Event 3: ProgressAgent (should be skipped)

    ctx.session.events = [
        Event(author="researcher", content=Content(parts=[Part(text="Chunk 1")])),
        Event(author="researcher", content=Content(parts=[Part(text=" Chunk 2")])),
        Event(
            author="progress_judge",
            content=Content(parts=[Part(text="⚖️ Evaluating...")]),
        ),
    ]

    # Run the capturer
    events = []
    async for event in capturer._run_async_impl(ctx):
        events.append(event)

    # Check that it captured BOTH chunks and accumulated them
    assert ctx.session.state.get("findings") == "Chunk 1 Chunk 2"
    assert events[0].content.parts[0].text == "Chunk 1 Chunk 2"


@pytest.mark.asyncio
async def test_state_capturer_skip_progress():
    """Test that StateCapturer skips progress messages."""
    capturer = StateCapturer(output_key="findings")
    ctx = MagicMock(spec=InvocationContext)
    ctx.session = MagicMock()
    ctx.session.state = {}

    ctx.session.events = [
        Event(
            author="researcher", content=Content(parts=[Part(text="Valid findings")])
        ),
        Event(
            author="orchestrator", content=Content(parts=[Part(text="🚀 Starting...")])
        ),
    ]

    async for _ in capturer._run_async_impl(ctx):
        pass

    assert ctx.session.state.get("findings") == "Valid findings"


@pytest.mark.asyncio
async def test_state_capturer_prefix_with_topic():
    """Test that StateCapturer correctly prefixes findings with the topic."""
    capturer = StateCapturer(output_key="findings", prefix_with_topic=True)
    ctx = MagicMock(spec=InvocationContext)
    ctx.session = MagicMock()
    ctx.session.state = {"topic": "AI Agents"}
    ctx.session.events = [
        Event(author="researcher", content=Content(parts=[Part(text="Deep research.")])),
    ]

    events = []
    async for event in capturer._run_async_impl(ctx):
        events.append(event)

    expected = "Topic: AI Agents\n\nFindings:\nDeep research."
    assert ctx.session.state.get("findings") == expected
    assert events[0].content.parts[0].text == expected


@pytest.mark.asyncio
async def test_state_capturer_prefer_history_over_empty_state():
    """Test that StateCapturer prefers history even if findings key exists but is empty."""
    capturer = StateCapturer(output_key="findings")
    ctx = MagicMock(spec=InvocationContext)
    ctx.session = MagicMock()
    ctx.session.state = {"findings": ""} # Empty state

    ctx.session.events = [
        Event(author="researcher", content=Content(parts=[Part(text="New Findings")])),
    ]

    async for _ in capturer._run_async_impl(ctx):
        pass

    assert ctx.session.state.get("findings") == "New Findings"
