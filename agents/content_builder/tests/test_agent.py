from agents.content_builder.agent import content_builder


def test_content_builder_agent_config():
    """Verify basic agent configuration."""
    assert content_builder.name == "content_builder"
    assert "Transforms research findings" in content_builder.description

def test_content_builder_agent_instruction_contains_keywords():
    """Verify that the instruction includes key formatting keywords."""
    instruction = content_builder.instruction.lower()
    assert "research findings" in instruction
    assert "h1" in instruction or "#" in instruction
    assert "h2" in instruction or "##" in instruction
    assert "bullet points" in instruction
