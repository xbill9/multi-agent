import logging
import os
from typing import Literal

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from pydantic import BaseModel, Field

from shared.logging_config import setup_logging

# Initialize standardized logging
setup_logging("judge")
logger = logging.getLogger(__name__)

MODEL = os.getenv("GENAI_MODEL", "gemini-2.5-flash")

class JudgeFeedback(BaseModel):
    """Feedback from the judge on the research quality."""
    status: Literal["pass", "fail"] = Field(description="The status of the research: 'pass' or 'fail'.")
    feedback: str = Field(description="Detailed feedback on the research findings.")

async def log_before_judge(callback_context: CallbackContext) -> None:
    """Log when the judge agent starts evaluation."""
    logger.info(f"Judge agent starting evaluation for session: {callback_context.session.id}")

async def log_after_judge(callback_context: CallbackContext) -> None:
    """Log the result of the judge's evaluation."""
    evaluation = callback_context.session.state.get("judge_evaluation")
    if evaluation:
        # Handle both dict and Pydantic object if needed
        is_dict = isinstance(evaluation, dict)
        status = evaluation.get("status") if is_dict else getattr(evaluation, "status", "unknown")
        feedback = evaluation.get("feedback") if is_dict else getattr(evaluation, "feedback", "")

        logger.info(f"Judge evaluation complete. Status: {status}")
        if status == "fail":
            logger.warning(f"Research failed validation. Feedback: {feedback}")
        else:
            logger.debug(f"Research passed validation. Feedback: {feedback}")

# Define the Judge Agent
judge = Agent(
    name="judge",
    model=MODEL,
    description="Evaluates research findings for accuracy and completeness.",
    instruction="""
    You are an expert editor and quality controller specialized in educational content. Your goal is to evaluate the research findings provided to you.

    Evaluation Criteria:
    1. **Accuracy**: Are the facts presented correct and verifiable?
    2. **Completeness**: Does the research cover all key aspects of the requested topic?
    3. **Structure**: Is the information organized logically for a course module?
    4. **Source Variety**: Does the research draw from multiple reliable sources (if applicable)?

    Decision Logic:
    - Set status to 'pass' ONLY if the research is high-quality and ready to be turned into a course module.
    - Set status to 'fail' if there are factual errors, missing sections, or if the information is too superficial.

    Feedback Requirements:
    - If 'fail', provide a numbered list of specific, actionable improvements needed.
    - If 'pass', briefly summarize why the research is sufficient for course creation.

    Always return your evaluation using the JudgeFeedback schema.
    If the input is empty or irrelevant to the topic, set status to 'fail' and request valid research findings.
    """,
    output_schema=JudgeFeedback,
    output_key="judge_evaluation",
    before_agent_callback=log_before_judge,
    after_agent_callback=log_after_judge,
)

logger.info(f"Initialized judge agent with model: {MODEL}")

root_agent = judge
