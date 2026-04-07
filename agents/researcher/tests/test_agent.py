from agents.researcher.agent import researcher


def test_researcher_initialization():
    """Test that the researcher agent is initialized correctly."""
    assert researcher.name == "researcher"
    assert "expert researcher" in researcher.instruction.lower()
    assert "google_search" in [tool.name for tool in researcher.tools]
