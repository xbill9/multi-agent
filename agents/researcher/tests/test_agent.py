from agents.researcher.agent import researcher


def test_researcher_initialization():
    """Test that the researcher agent is initialized correctly."""
    assert researcher.name == "researcher"
    assert "professional researcher" in researcher.instruction.lower()
    # Check for both full path and short name in case of ADK version variations
    tool_names = [tool.name for tool in researcher.tools]
    assert any("google_search" in name for name in tool_names)


def test_researcher_instruction_guidelines():
    """Test that the researcher instructions contain required guidelines."""
    instruction = researcher.instruction.lower()
    assert "citations" in instruction
    assert "markdown" in instruction
