import logging
import os

from google.adk.agents import Agent
from google.adk.tools import google_search

from shared.logging_config import setup_logging

# --- Configuration & Environment ---
os.environ["ADK_SUPPRESS_EXPERIMENTAL_FEATURE_WARNINGS"] = "True"
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "False")

from google.adk.agents.callback_context import CallbackContext
from google.genai import types as genai_types

# Initialize standardized logging
setup_logging("researcher")
logger = logging.getLogger(__name__)

async def log_before_researcher(callback_context: CallbackContext) -> None:
    """Ensure topic is correctly identified and passed to the model."""
    try:
        logger.info(f"Researcher starting for session: {callback_context.session.id}")

        # Prioritize topic from state
        state_dict = callback_context.state.to_dict()
        topic = state_dict.get("topic")

        # Extraction logic for history/metadata
        if not topic or any(x in str(topic) for x in ["said:", "[", "]"]):
            if callback_context.user_content and callback_context.user_content.parts:
                for part in callback_context.user_content.parts:
                    if part.text:
                        text = part.text.replace("For context:", "").strip()
                        if "said:" in text:
                            text = text.split("said:", 1)[1].strip()
                        if text and not any(e in text for e in ["🔍", "⚖️", "🚀", "✍️", "⌛", "[SYSTEM]"]):
                            topic = text
                            callback_context.session.state["topic"] = topic
                            break

        if topic:
            logger.info(f"[RESEARCHER] Active topic: '{topic}'")
            # Update in-place
            callback_context.user_content.parts = [
                genai_types.Part(text=f"Produce a comprehensive Markdown research report on the following topic: {topic}. Use the google_search tool if available, otherwise use your internal knowledge. Include history, key figures, and impact.")
            ]
        else:
            logger.error("[RESEARCHER] No topic found!")
    except Exception as e:
        logger.exception(f"[RESEARCHER] Error in before_agent_callback: {e}")

async def log_after_researcher(callback_context: CallbackContext) -> None:
    """Log the output of the researcher."""
    try:
        # Diagnostic: what attributes do we have?
        # logger.info(f"Researcher callback attributes: {dir(callback_context)}")

        # In newer ADK versions, response might be in 'response'
        response = getattr(callback_context, "response", None)
        if response and hasattr(response, "parts"):
            text = "".join([p.text for p in response.parts if p.text])
            logger.info(f"Researcher finished. Output length: {len(text)}")
        else:
            logger.warning("Researcher callback: 'response' not found or has no parts.")
    except Exception as e:
        logger.error(f"Error in log_after_researcher: {e}")
    return None

# Use Flash for speed
MODEL = os.getenv("GENAI_MODEL", "gemini-2.5-flash")

# Define the Researcher Agent
researcher = Agent(
    name="researcher",
    model=MODEL,
    description="Gathers information on a topic.",
    instruction="You are a professional researcher. Always provide a detailed Markdown report with multiple sections and citations/sources.",
    tools=[google_search],
    before_agent_callback=log_before_researcher,
    after_agent_callback=log_after_researcher,
)

logger.info(f"Initialized researcher agent with model: {MODEL}")

root_agent = researcher
