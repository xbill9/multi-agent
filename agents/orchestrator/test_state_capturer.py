import pytest
import json
from unittest.mock import MagicMock
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
        Event(author="progress_judge", content=Content(parts=[Part(text="⚖️ Evaluating...")])),
    ]
    
    # Run the capturer
    events = []
    async for event in capturer._run_async_impl(ctx):
        events.append(event)
    
    # Check that it captured "Chunk 1 Chunk 2"
    # Actually, the CURRENT StateCapturer only takes the LAST one.
    # Let's see what it does.
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
        Event(author="researcher", content=Content(parts=[Part(text="Valid findings")])),
        Event(author="orchestrator", content=Content(parts=[Part(text="🚀 Starting...")])),
    ]
    
    async for _ in capturer._run_async_impl(ctx):
        pass
    
    assert ctx.session.state.get("findings") == "Valid findings"

@pytest.mark.asyncio
async def test_state_capturer_prefer_state_bug():
    """Test the bug where it prefers state even if we want to capture new findings."""
    capturer = StateCapturer(output_key="findings")
    ctx = MagicMock(spec=InvocationContext)
    ctx.session = MagicMock()
    # State already has old findings
    ctx.session.state = {"findings": "Old Findings"}
    
    # History has NEW findings
    ctx.session.events = [
        Event(author="researcher", content=Content(parts=[Part(text="New Findings")])),
    ]
    
    async for _ in capturer._run_async_impl(ctx):
        pass
    
    # It SHOULD be "New Findings", but the current code will keep "Old Findings"
    assert ctx.session.state.get("findings") == "New Findings"
