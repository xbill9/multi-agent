import logging
import os

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types as genai_types

from shared.logging_config import setup_logging

# Initialize standardized logging
setup_logging("content_builder")
logger = logging.getLogger(__name__)

async def log_before_agent(callback_context: CallbackContext) -> None:
    """Log before the agent starts and inject research findings into the context."""
    logger.info(f"Agent {callback_context.agent_name} starting execution. Session: {callback_context.session}")
    state_dict = callback_context.state.to_dict()

    if "research_findings" in state_dict:
        findings = state_dict['research_findings']
        logger.info(f"Injecting research_findings into user context (length: {len(str(findings))})")

        # Inject the findings into the first user message part to ensure the LLM sees them
        if callback_context.user_content and callback_context.user_content.parts:
            original_text = callback_context.user_content.parts[0].text or ""
            callback_context.user_content.parts[0].text = f"RESEARCH FINDINGS:\n{findings}\n\nUSER QUERY:\n{original_text}"
    else:
        logger.warning("research_findings NOT found in state!")

async def log_after_agent(callback_context: CallbackContext) -> genai_types.Content | None:
    """Log after the agent finishes."""
    logger.info(f"Agent {callback_context.agent_name} finished execution.")
    return None

MODEL = os.getenv("GENAI_MODEL", "gemini-2.5-flash")

# Define the Content Builder Agent
content_builder = Agent(
    name="content_builder",
    model=MODEL,
    description="Transforms research findings into high-quality Markdown course modules.",
    instruction="""
    You are an expert content builder. Your goal is to transform research findings into a structured course module.

    CRITICAL: The research findings are provided in the session state variable `research_findings`.
    You MUST read these findings from the state and use them as the primary source for the course content.

    Use H1 for the module title, H2 for main sections, and bullet points for lists.
    Ensure that the content is accurate and easy to read.
    Format the findings clearly using Markdown.
    """,
    tools=[],
    before_agent_callback=log_before_agent,
    after_agent_callback=log_after_agent,
)

logger.info(f"Initialized content_builder agent with model: {MODEL}")

root_agent = content_builder
