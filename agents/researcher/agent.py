import logging
import os

from google.adk.agents import Agent
from google.adk.tools.google_search_tool import google_search

from shared.logging_config import setup_logging

# Initialize standardized logging
setup_logging("researcher")
logger = logging.getLogger(__name__)

MODEL = os.getenv("GENAI_MODEL", "gemini-2.5-flash")

# Define the Researcher Agent
researcher = Agent(
    name="researcher",
    model=MODEL,
    description="Gathers information on a topic using Google Search.",
    instruction="""
    You are an expert researcher. Your goal is to find comprehensive and accurate information on the user's topic.
    Use the `google_search` tool to find relevant information.
    Summarize your findings clearly.
    If you receive feedback that your research is insufficient, use the feedback to refine your next search.
    """,
    tools=[google_search],
)

logger.info(f"Initialized researcher agent with model: {MODEL}")

root_agent = researcher

