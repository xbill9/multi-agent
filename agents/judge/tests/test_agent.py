from agents.judge.agent import judge


def test_judge_initialization():
    """Test that the judge agent is initialized correctly."""
    assert judge.name == "judge"
    assert "quality controller" in judge.instruction.lower()
    assert judge.output_schema is not None
    assert judge.output_schema.__name__ == "JudgeFeedback"
