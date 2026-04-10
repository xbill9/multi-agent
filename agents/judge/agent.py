import logging
import os
from typing import Literal
from datetime import datetime

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types as genai_types
from pydantic import BaseModel, Field

from shared.logging_config import setup_logging

# Initialize standardized logging
setup_logging("judge")
logger = logging.getLogger(__name__)

MODEL = os.getenv("GENAI_MODEL", "gemini-2.5-flash")


class JudgeFeedback(BaseModel):
    """Feedback from the judge on the research quality."""

    status: Literal["pass", "fail"] = Field(
        description="The status of the research: 'pass' or 'fail'."
    )
    feedback: str = Field(description="Detailed feedback on the research findings.")


async def log_before_judge(
    callback_context: CallbackContext,
) -> genai_types.Content | None:
    """Ensure research findings are correctly identified for evaluation."""
    logger.info(f"Judge starting for session: {callback_context.session.id}")

    # Dynamically get the current date
    current_date = datetime.now().strftime("%A, %B %d, %Y")

    # Prioritize findings from state (if shared)
    state_dict = callback_context.state.to_dict()
    findings = state_dict.get("research_findings")

    # Extraction logic for history/metadata
    if not findings or len(str(findings)) < 100:
        if callback_context.user_content and callback_context.user_content.parts:
            # Look for the most substantial text part (likely the research report)
            potential_findings = []
            for part in callback_context.user_content.parts:
                if part.text:
                    text = part.text.replace("For context:", "").strip()
                    if "said:" in text:
                        text = text.split("said:", 1)[1].strip()

                    # Heuristic: Research reports are usually long and have Markdown
                    if len(text) > 500:
                        potential_findings.append(text)

            if potential_findings:
                findings = potential_findings[-1]
                callback_context.session.state["research_findings"] = findings
                logger.info(
                    f"[JUDGE] Recovered findings from history (length: {len(findings)})"
                )

    if findings and len(str(findings)) > 200:
        logger.info(f"[JUDGE] Evaluating research (length: {len(str(findings))})")
        callback_context.user_content.parts = [
            genai_types.Part(
                text=f"CURRENT CONTEXT: Today is {current_date}.\n"
                     f"Treat 2025 and early 2026 events as established historical facts.\n\n"
                     f"Please evaluate the following research findings:\n\n{findings}"
            )
        ]
    else:
        logger.error("[JUDGE] No substantial research findings found to evaluate!")
        callback_context.user_content.parts = [
            genai_types.Part(
                text="ERROR: No research findings were provided for evaluation. Please conduct research first."
            )
        ]
    return None


async def log_after_judge(callback_context: CallbackContext) -> None:
    """Log the result of the judge's evaluation."""
    evaluation = callback_context.session.state.get("judge_evaluation")
    if evaluation:
        # Handle both dict and Pydantic object if needed
        is_dict = isinstance(evaluation, dict)
        status = (
            evaluation.get("status")
            if is_dict
            else getattr(evaluation, "status", "unknown")
        )
        feedback = (
            evaluation.get("feedback")
            if is_dict
            else getattr(evaluation, "feedback", "")
        )

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
    - Set status to 'fail' if the findings are just a generic response saying they are ready to research (e.g. "I am ready to conduct...").

    Feedback Requirements:
    - If 'fail', provide a numbered list of specific, actionable improvements needed.
    - If 'pass', briefly summarize why the research is sufficient for course creation.

    Always return your evaluation using the JudgeFeedback schema.
    If the input is empty, irrelevant, or just a placeholder message, set status to 'fail' and demand comprehensive research findings on the actual topic.
    """,
    output_schema=JudgeFeedback,
    output_key="judge_evaluation",
    before_agent_callback=log_before_judge,
    after_agent_callback=log_after_judge,
)

logger.info(f"Initialized judge agent with model: {MODEL}")

root_agent = judge
