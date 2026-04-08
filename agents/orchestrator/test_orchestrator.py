from unittest.mock import MagicMock

import pytest
from google.adk.agents.invocation_context import InvocationContext

from agents.orchestrator.agent import escalation_checker


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
    assert "Research approved" in events[0].content.parts[0].text


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
    # ADK actions might be None for escalate by default or have escalate=False
    assert events[0].actions is None or events[0].actions.escalate in (None, False)
    assert "Research needs more work" in events[0].content.parts[0].text


@pytest.mark.asyncio
async def test_escalation_checker_string_pass():
    """Test that EscalationChecker handles string feedback containing 'pass'."""
    ctx = MagicMock(spec=InvocationContext)
    ctx.session = MagicMock()
    ctx.session.state = {
        "judge_feedback": '{"status": "pass", "feedback": "Great job"}'
    }

    events = []
    async for event in escalation_checker._run_async_impl(ctx):
        events.append(event)

    assert len(events) == 1
    assert events[0].actions.escalate is True
    assert "Research approved" in events[0].content.parts[0].text


@pytest.mark.asyncio
async def test_escalation_checker_pass_uppercase():
    """Test that EscalationChecker handles uppercase 'PASS'."""
    ctx = MagicMock(spec=InvocationContext)
    ctx.session = MagicMock()
    ctx.session.state = {"judge_feedback": {"status": "PASS"}}

    events = []
    async for event in escalation_checker._run_async_impl(ctx):
        events.append(event)

    assert len(events) == 1
    assert events[0].actions.escalate is True


@pytest.mark.asyncio
async def test_escalation_checker_string_plain_pass():
    """Test that EscalationChecker handles plain string feedback containing 'status: pass'."""
    ctx = MagicMock(spec=InvocationContext)
    ctx.session = MagicMock()
    ctx.session.state = {"judge_feedback": "Research is complete. Status: pass"}

    events = []
    async for event in escalation_checker._run_async_impl(ctx):
        events.append(event)

    assert len(events) == 1
    assert events[0].actions.escalate is True
