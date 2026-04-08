import logging
import os

from google.adk.agents import Agent
from google.adk.tools import google_search

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

    ### STEP-BY-STEP:
    1. **Initial Search**: Use the `google_search` tool to gather broad information.
    2. **Analysis**: Critically analyze the search results. If the tool returns irrelevant information (e.g., only current time for a history query), do NOT accept it as a valid answer.
    3. **Refined Search**: If the initial results are insufficient or irrelevant, try at least one more search with a different, more specific query.
    4. **Synthesis & Fallback**:
       - If search succeeds, summarize the findings with **citations** and source URLs.
       - If the search tool consistently fails or provides irrelevant results, use your extensive internal knowledge to provide a comprehensive and accurate report.
       - Clearly state if you are using internal knowledge due to technical limitations with the information retrieval tool.

    ### CRITICAL:
    - Your response MUST be a detailed Markdown report covering history, geography, culture, economy, and landmarks where applicable.
    - **Citations**: ALWAYS include a 'Sources' or 'References' section at the end. If based on internal knowledge, cite general historical and geographical consensus.
    - Do NOT just list search queries.
    - Ensure the report is high-quality and ready to be used by a content builder for a course module.
    """,
    tools=[google_search],
)

logger.info(f"Initialized researcher agent with model: {MODEL}")

root_agent = researcher
