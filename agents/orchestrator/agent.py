import json
import logging
import os
from collections.abc import AsyncGenerator

from google.adk.agents import BaseAgent, LoopAgent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.events import Event, EventActions

from shared.authenticated_httpx import create_authenticated_client

logger = logging.getLogger(__name__)


# --- Callbacks ---
def create_save_output_callback(key: str):
    """Creates a callback to save the agent's final response to session state."""
    def callback(callback_context: CallbackContext, **kwargs) -> None:
        ctx = callback_context
        # Find the last event from this agent that has content
        for event in reversed(ctx.session.events):
            if event.author == ctx.agent_name and event.content and event.content.parts:
                text = event.content.parts[0].text
                if text:
                    # Try to parse as JSON if it looks like it, for judge_feedback
                    if key == "judge_feedback" and text.strip().startswith("{"):
                        try:
                            ctx.state[key] = json.loads(text)
                        except json.JSONDecodeError:
                            ctx.state[key] = text
                    else:
                        ctx.state[key] = text
                    logger.info(f"Saved output to state['{key}']", extra={"agent": ctx.agent_name})
                    return
    return callback

# --- Remote Agents ---

# Connect to the Researcher (Localhost port 8001)
researcher_url = os.environ.get("RESEARCHER_AGENT_CARD_URL", "http://localhost:8001/a2a/agent/.well-known/agent-card.json")
researcher = RemoteA2aAgent(
    name="researcher",
    agent_card=researcher_url,
    description="Gathers information using Google Search.",
    # IMPORTANT: Save the output to state for the Judge to see
    after_agent_callback=create_save_output_callback("research_findings"),
    # IMPORTANT: Use authenticated client for communication
    httpx_client=create_authenticated_client(researcher_url),
    use_legacy=False
)

# Connect to the Judge (Localhost port 8002)
judge_url = os.environ.get("JUDGE_AGENT_CARD_URL", "http://localhost:8002/a2a/agent/.well-known/agent-card.json")
judge = RemoteA2aAgent(
    name="judge",
    agent_card=judge_url,
    description="Evaluates research.",
    after_agent_callback=create_save_output_callback("judge_feedback"),
    httpx_client=create_authenticated_client(judge_url),
    use_legacy=False
)

# Content Builder (Localhost port 8003)
content_builder_url = os.environ.get("CONTENT_BUILDER_AGENT_CARD_URL", "http://localhost:8003/a2a/agent/.well-known/agent-card.json")
content_builder = RemoteA2aAgent(
    name="content_builder",
    agent_card=content_builder_url,
    description="Builds the course.",
    httpx_client=create_authenticated_client(content_builder_url),
    use_legacy=False
)

# --- Escalation Checker ---

class EscalationChecker(BaseAgent):
    """Checks the judge's feedback and escalates (breaks the loop) if it passed."""

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event]:
        # Retrieve the feedback saved by the Judge
        feedback = ctx.session.state.get("judge_feedback")
        logger.info(f"Processing feedback: {feedback}", extra={"agent": self.name})

        # Check for 'pass' status
        is_pass = False
        if isinstance(feedback, dict) and feedback.get("status") == "pass":
            is_pass = True
        # Handle string fallback if JSON parsing failed
        elif isinstance(feedback, str) and '"status": "pass"' in feedback:
            is_pass = True

        if is_pass:
            logger.info("Research approved, escalating...", extra={"agent": self.name})
            # 'escalate=True' tells the parent LoopAgent to stop looping
            yield Event(
                author=self.name,
                actions=EventActions(escalate=True),
                content={"parts": [{"text": "Research approved. Escalating to Content Builder."}]}
            )
        else:
            logger.info("Research needs more work, continuing loop...", extra={"agent": self.name})
            # Continue the loop
            yield Event(
                author=self.name,
                content={"parts": [{"text": "Research needs more work. Continuing research loop."}]}
            )

escalation_checker = EscalationChecker(name="escalation_checker")

# --- Orchestration ---

research_loop = LoopAgent(
    name="research_loop",
    description="Iteratively researches and judges until quality standards are met.",
    sub_agents=[researcher, judge, escalation_checker],
    max_iterations=3,
)

root_agent = SequentialAgent(
    name="course_creation_pipeline",
    description="A pipeline that researches a topic and then builds a course from it.",
    sub_agents=[research_loop, content_builder],
)

agent = root_agent

