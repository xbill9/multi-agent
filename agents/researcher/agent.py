import logging
import os
import asyncio

from google.adk.agents import Agent
from google.adk.tools import google_search
from google.genai import types

from shared.logging_config import setup_logging

# --- Configuration & Environment ---
os.environ["ADK_SUPPRESS_EXPERIMENTAL_FEATURE_WARNINGS"] = "True"
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "False")

# Initialize standardized logging
setup_logging("researcher")
logger = logging.getLogger(__name__)

# Use Pro for better synthesis
MODEL = os.getenv("GENAI_MODEL", "gemini-2.5-flash")

# Define the Researcher Agent
researcher = Agent(
    name="researcher",
    model=MODEL,
    description="Gathers information on a topic using Google Search.",
    instruction="""
    You are an expert researcher. Your goal is to find comprehensive and accurate information on the user's topic.
    
    STEP-BY-STEP:
    1. Use the `google_search` tool.
    2. Analyze the search results.
    3. You MUST provide a full summary of the information you found.
    4. If you only see search suggestions, you MUST use them to perform another search to get actual content.
    
    CRITICAL: Your response MUST be a detailed Markdown report. Do NOT just list search queries.
    """,
    tools=[google_search],
)

logger.info(f"Initialized researcher agent with model: {MODEL}")

root_agent = researcher
