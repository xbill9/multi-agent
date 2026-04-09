import pytest

from agents.judge.agent import judge, log_after_judge


def test_judge_initialization():
    """Test that the judge agent is initialized correctly."""
    assert judge.name == "judge"
    assert "quality controller" in judge.instruction.lower()
    assert judge.output_schema is not None
    assert judge.output_schema.__name__ == "JudgeFeedback"


@pytest.mark.anyio
async def test_log_after_judge_dict(caplog):
    """Test log_after_judge with a dictionary in state."""
    from unittest.mock import MagicMock

    from google.adk.agents.callback_context import CallbackContext

    mock_ctx = MagicMock(spec=CallbackContext)
    mock_ctx.session.state = {"judge_evaluation": {"status": "pass", "feedback": "Good job"}}

    with caplog.at_level("INFO"):
        await log_after_judge(mock_ctx)

    assert "Judge evaluation complete. Status: pass" in caplog.text


@pytest.mark.anyio
async def test_log_after_judge_object(caplog):
    """Test log_after_judge with a Pydantic-like object in state."""
    from unittest.mock import MagicMock

    from google.adk.agents.callback_context import CallbackContext

    class MockFeedback:
        def __init__(self, status):
            self.status = status

    mock_ctx = MagicMock(spec=CallbackContext)
    mock_ctx.session.state = {"judge_evaluation": MockFeedback(status="fail")}

    with caplog.at_level("INFO"):
        await log_after_judge(mock_ctx)

    assert "Judge evaluation complete. Status: fail" in caplog.text
