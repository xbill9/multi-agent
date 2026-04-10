import logging
import os

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types as genai_types

from shared.logging_config import setup_logging

# Initialize standardized logging
setup_logging("content_builder")
logger = logging.getLogger(__name__)

async def log_before_agent(callback_context: CallbackContext) -> genai_types.Content | None:
    """Ensure research findings are correctly identified for content generation."""
    try:
        logger.info(f"Content Builder starting for session: {callback_context.session.id}")
        
        state_dict = callback_context.state.to_dict()
        topic = state_dict.get("topic")
        findings = state_dict.get("research_findings")
        
        # Topic Recovery Heuristic
        if not topic or "UNKNOWN" in str(topic):
            if callback_context.user_content and callback_context.user_content.parts:
                for part in callback_context.user_content.parts:
                    if part.text:
                        text = part.text.replace("For context:", "").strip()
                        if "said:" in text: text = text.split("said:", 1)[1].strip()
                        # Topic is usually short and at the beginning of history
                        if text and len(text) > 2 and len(text) < 100 and not any(e in text for e in ["🔍", "⚖️"]):
                            topic = text
                            break
        
        if not topic: topic = "the requested topic"

        # Findings Recovery (if not in state)
        if not findings or len(str(findings)) < 500:
            if callback_context.user_content and callback_context.user_content.parts:
                for part in callback_context.user_content.parts:
                    if part.text:
                        text = part.text.replace("For context:", "").strip()
                        if "said:" in text: text = text.split("said:", 1)[1].strip()
                        if len(text) > 1000: # High threshold for actual report
                            findings = text
                            break

        if findings and len(str(findings)) > 200:
            logger.info(f"Building course for topic '{topic}' (findings len: {len(str(findings))})")
            # PASS ONLY FINDINGS AND TOPIC
            callback_context.user_content.parts = [genai_types.Part(text=f"Target Topic: {topic}\n\nResearch Findings:\n{findings}")]
        else:
            logger.error("No findings found!")
            callback_context.user_content.parts = [genai_types.Part(text="ERROR: No research findings available.")]
        return None
    except Exception as e:
        logger.exception(f"Error in Content Builder callback: {e}")
        return None

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
    You are an expert content builder. 
    
    TASK: Transform the provided RESEARCH FINDINGS into a comprehensive Markdown course about the TARGET TOPIC.
    
    CRITICAL CONSTRAINTS:
    1. START your response immediately with the Course Title using an H1 header (#).
    2. DO NOT include any introductory text, preamble, or meta-commentary.
    3. DO NOT echo the input findings, headers, or instructions.
    4. FORMAT: Use H1 for Title, H2 for Modules, H3 for Sub-sections. Use bullet points for lists.
    5. INTEGRITY: Ensure the output is a single, clean Markdown document with NO meta-data or labels.
    """,
    tools=[],
    before_agent_callback=log_before_agent,
    after_agent_callback=log_after_agent,
)

logger.info(f"Initialized content_builder agent with model: {MODEL}")

root_agent = content_builder
