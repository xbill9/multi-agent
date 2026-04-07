import logging
import os

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
    status: str = Field(description="The status of the research: 'pass' or 'fail'.")
    feedback: str = Field(description="Detailed feedback on the research findings.")

async def log_before_judge(callback_context: CallbackContext) -> None:
    """Log when the judge agent starts evaluation."""
    logger.info(f"Judge agent starting evaluation for session: {callback_context.session.id}")

async def log_after_judge(callback_context: CallbackContext) -> None:
    """Log the result of the judge's evaluation."""
    # The structured output is stored in ctx.session.state by the Agent
    # if output_key is not specified, it's not automatically stored in state by default Agent behavior,
    # but the final response contains it.
    # However, for logging purposes, we can see if it was placed in state if we had an output_key.
    # Let's add an output_key to make it easier to log from the callback.
    evaluation = callback_context.session.state.get("judge_evaluation")
    if evaluation:
        logger.info(f"Judge evaluation complete. Status: {evaluation.get('status')}")
        logger.debug(f"Full feedback: {evaluation.get('feedback')}")

# Define the Judge Agent
judge = Agent(
    name="judge",
    model=MODEL,
    description="Evaluates research findings for accuracy and completeness.",
    instruction="""
    You are an expert editor and quality controller. Your goal is to evaluate the research findings provided to you.
    Check for accuracy, completeness, and relevance to the topic.
    If the research is sufficient, set status to 'pass'.
    If the research is insufficient or inaccurate, set status to 'fail' and provide specific feedback for improvement.
    Always return your evaluation using the JudgeFeedback schema.
    """,
    output_schema=JudgeFeedback,
    output_key="judge_evaluation",
    before_agent_callback=log_before_judge,
    after_agent_callback=log_after_judge,
)

logger.info(f"Initialized judge agent with model: {MODEL}")

root_agent = judge
