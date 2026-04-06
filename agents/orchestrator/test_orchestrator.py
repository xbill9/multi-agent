import pytest
from agents.orchestrator.agent import escalation_checker
from google.adk.agents.invocation_context import InvocationContext
from unittest.mock import MagicMock

@pytest.mark.asyncio
async def test_escalation_checker_pass():
    """Test that EscalationChecker yields an escalate event when feedback is 'pass'."""
    # Mock context with session state
    ctx = MagicMock(spec=InvocationContext)
    ctx.session = MagicMock()
    ctx.session.state = {"judge_feedback": {"status": "pass"}}
    
    events = []
    async for event in escalation_checker._run_async_impl(ctx):
        events.append(event)
    
    assert len(events) == 1
    assert events[0].actions.escalate is True

@pytest.mark.asyncio
async def test_escalation_checker_fail():
    """Test that EscalationChecker does NOT yield an escalate event when feedback is 'fail'."""
    ctx = MagicMock(spec=InvocationContext)
    ctx.session = MagicMock()
    ctx.session.state = {"judge_feedback": {"status": "fail"}}
    
    events = []
    async for event in escalation_checker._run_async_impl(ctx):
        events.append(event)
    
    assert len(events) == 1
    # ADK actions might have None for escalate by default
    assert events[0].actions is None or events[0].actions.escalate in (None, False)

@pytest.mark.asyncio
async def test_escalation_checker_string_pass():
    """Test that EscalationChecker handles string feedback containing 'pass'."""
    ctx = MagicMock(spec=InvocationContext)
    ctx.session = MagicMock()
    ctx.session.state = {"judge_feedback": '{"status": "pass", "feedback": "Great job"}'}
    
    events = []
    async for event in escalation_checker._run_async_impl(ctx):
        events.append(event)
    
    assert len(events) == 1
    assert events[0].actions.escalate is True
