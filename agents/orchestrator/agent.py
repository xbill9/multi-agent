import json
import logging
import os
from collections.abc import AsyncGenerator

from google.adk.agents import BaseAgent, LoopAgent, SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.events import Event, EventActions
from google.genai.types import Content, Part
from pydantic import PrivateAttr

from shared.authenticated_httpx import create_authenticated_client

logger = logging.getLogger(__name__)

# --- Custom Orchestration Components ---


class TopicCapturer(BaseAgent):
    """Captures the initial user topic into state."""

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event]:
        topic = ""
        if ctx.user_content and ctx.user_content.parts:
            # Look for the FIRST part that isn't metadata
            for part in ctx.user_content.parts:
                if part.text and not part.text.strip().startswith(
                    ("For context:", "[SYSTEM]")
                ):
                    topic = part.text.strip()
                    break

        # Clean up the topic (remove "Create a course on: " prefix from frontend)
        if topic:
            import re

            topic = re.sub(
                r"Create a comprehensive course on:\s*", "", topic, flags=re.IGNORECASE
            ).strip()

        if topic:
            ctx.session.state["topic"] = topic
            logger.info(f"[TopicCapturer] Current topic set to: '{topic}'")
            # Return a clean event with JUST the topic
            yield Event(author=self.name, content=Content(parts=[Part(text=topic)]))
        else:
            logger.error("[TopicCapturer] No topic provided in user message!")
            # Check if we have it in state already
            topic = ctx.session.state.get("topic")
            if topic:
                logger.info(
                    f"[TopicCapturer] Using existing topic from state: '{topic}'"
                )
                yield Event(author=self.name, content=Content(parts=[Part(text=topic)]))
            else:
                yield Event(
                    author=self.name,
                    content=Content(
                        parts=[
                            Part(
                                text="❌ ERROR: No topic detected. Please provide a subject to research (e.g., 'Curling' or 'Quantum Physics')."
                            )
                        ]
                    ),
                )


class StateCapturer(BaseAgent):
    """Captures the last text output from the session history into state."""

    _output_key: str = PrivateAttr()
    _restore_from_state: bool = PrivateAttr()
    _author_filter: str | None = PrivateAttr()
    _prefix_with_topic: bool = PrivateAttr()

    def __init__(
        self,
        output_key: str,
        restore_from_state: bool = False,
        author_filter: str | None = None,
        prefix_with_topic: bool = False,
    ):
        super().__init__(name=f"capture_{output_key}")
        self._output_key = output_key
        self._restore_from_state = restore_from_state
        self._author_filter = author_filter
        self._prefix_with_topic = prefix_with_topic

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event]:
        text = ""
        logger.info(
            f"[{self.name}] Scanning history for key: {self._output_key}. Author filter: {self._author_filter}"
        )

        if self._restore_from_state and ctx.session.state.get(self._output_key):
            text = str(ctx.session.state.get(self._output_key))
            logger.info(f"[{self.name}] Restoring from state: {len(text)} chars")

        if not text and ctx.session.events:
            scanning_author = None
            # Scan backwards to find the latest block of content from the target author
            for event in reversed(ctx.session.events):
                if event.author == self.name or "progress" in event.author.lower():
                    continue

                # Apply author filter if provided
                if self._author_filter and event.author != self._author_filter:
                    if scanning_author:
                        # We hit a different author after starting to capture a block
                        break
                    continue

                if event.content and event.content.parts:
                    event_text = ""
                    for part in event.content.parts:
                        if part.text:
                            # CRITICAL: Exclude system-added "For context:" and emojis
                            clean_text = part.text.replace("For context:", "").strip()
                            if clean_text and not clean_text.startswith(
                                ("🔍", "⚖️", "🚀", "✍️", "⌛", "[SYSTEM]")
                            ):
                                event_text += clean_text + " "

                    if event_text.strip():
                        if not scanning_author:
                            scanning_author = event.author
                            logger.info(
                                f"[{self.name}] Found latest author: {scanning_author}"
                            )

                        if event.author == scanning_author:
                            # Accumulate - prepend since we are scanning backwards
                            text = event_text.strip() + (" " + text if text else "")
                        else:
                            # Hit a different author block
                            break

            if text:
                logger.info(
                    f"[{self.name}] ✅ Captured content from {scanning_author} (total length: {len(text)})"
                )

        if text:
            # Optionally prefix with topic for content building
            if self._prefix_with_topic:
                topic = ctx.session.state.get("topic")
                if topic:
                    text = f"Topic: {topic}\n\nFindings:\n{text}"
                    logger.info(f"[{self.name}] Prefixed with topic: {topic}")

            # Try to parse as JSON if it looks like it and we don't already have it as a dict
            if not isinstance(
                ctx.session.state.get(self._output_key), dict
            ) and text.startswith("{"):
                try:
                    ctx.session.state[self._output_key] = json.loads(text)
                except json.JSONDecodeError:
                    ctx.session.state[self._output_key] = text
            else:
                ctx.session.state[self._output_key] = text

            logger.info(
                f"[{self.name}] Persisted {self._output_key} to session state (length: {len(str(text))})."
            )
            # Yield the ACTUAL content so the next agent in sequence receives it!
            yield Event(author=self.name, content=Content(parts=[Part(text=str(text))]))
        else:
            logger.warning(
                f"[{self.name}] No content found to capture for {self._output_key}"
            )
            yield Event(
                author=self.name,
                content=Content(
                    parts=[
                        Part(
                            text=f"[SYSTEM] ERROR: Failed to capture {self._output_key}"
                        )
                    ]
                ),
            )


class EscalationChecker(BaseAgent):
    """Checks the Judge's feedback in session state and signals loop termination."""

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event]:
        # Try finding feedback in multiple locations for robustness
        feedback = ctx.session.state.get("judge_feedback") or ctx.session.state.get(
            "judge_evaluation"
        )

        if not feedback and ctx.user_content and ctx.user_content.parts:
            # Fallback to current user_content if not in state
            text = ctx.user_content.parts[0].text
            if text and text.strip().startswith("{"):
                try:
                    feedback = json.loads(text)
                except Exception:
                    feedback = text

        is_pass = False
        if isinstance(feedback, dict):
            status = str(feedback.get("status", "")).lower()
            if status == "pass":
                is_pass = True
        elif isinstance(feedback, str):
            feedback_lower = feedback.lower()
            if (
                '"status": "pass"' in feedback_lower
                or '"status":"pass"' in feedback_lower
            ):
                is_pass = True
            elif "status" in feedback_lower and "pass" in feedback_lower:
                import re

                if re.search(r'"status"\s*:\s*"pass"', feedback_lower) or re.search(
                    r"status\s*:\s*pass", feedback_lower
                ):
                    is_pass = True

        if is_pass:
            logger.info("[EscalationChecker] Research approved. ESCALATING.")
            yield Event(
                author=self.name,
                actions=EventActions(escalate=True),
                content=Content(
                    parts=[Part(text="Research approved. Moving to content builder.")]
                ),
            )
        else:
            logger.info(
                "[EscalationChecker] Research needs refinement. CONTINUING LOOP."
            )
            yield Event(
                author=self.name,
                content=Content(
                    parts=[Part(text="Research needs more work. Refining search...")]
                ),
            )


escalation_checker = EscalationChecker(name="escalation_checker")


class ProgressAgent(BaseAgent):
    """Simple agent that yields a progress message."""

    _message: str = PrivateAttr()
    _author: str = PrivateAttr()

    def __init__(self, message: str, author: str = "orchestrator"):
        super().__init__(name=f"progress_{author}")
        self._message = message
        self._author = author

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event]:
        logger.info(f"[Progress] {self._message}")
        # Yield the progress message for the UI
        yield Event(
            author=f"progress_{self._author}",
            content=Content(parts=[Part(text=self._message)]),
        )


# --- Remote Agents ---

researcher_url = os.environ.get(
    "RESEARCHER_AGENT_CARD_URL",
    "http://localhost:8001/a2a/researcher/.well-known/agent-card.json",
)
researcher = RemoteA2aAgent(
    name="researcher",
    agent_card=researcher_url,
    description="Gathers information using Google Search.",
    httpx_client=create_authenticated_client(researcher_url),
)

judge_url = os.environ.get(
    "JUDGE_AGENT_CARD_URL",
    "http://localhost:8002/a2a/judge/.well-known/agent-card.json",
)
judge = RemoteA2aAgent(
    name="judge",
    agent_card=judge_url,
    description="Evaluates research quality.",
    httpx_client=create_authenticated_client(judge_url),
)

content_builder_url = os.environ.get(
    "CONTENT_BUILDER_AGENT_CARD_URL",
    "http://localhost:8003/a2a/content_builder/.well-known/agent-card.json",
)
content_builder = RemoteA2aAgent(
    name="content_builder",
    agent_card=content_builder_url,
    description="Transforms research into a course module.",
    httpx_client=create_authenticated_client(content_builder_url),
)

# --- Orchestration ---

research_loop = LoopAgent(
    name="research_loop",
    description="Iteratively researches and judges findings.",
    sub_agents=[
        ProgressAgent("🔍 Research is starting...", author="researcher"),
        researcher,
        StateCapturer(output_key="research_findings", author_filter="researcher"),
        ProgressAgent("⚖️ Judge is evaluating findings...", author="judge"),
        judge,
        StateCapturer(output_key="judge_feedback", author_filter="judge"),
        EscalationChecker(name="escalation_checker"),
    ],
    max_iterations=2,
)


class ResearchGuard(BaseAgent):
    """Ensures research was successful before proceeding."""

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event]:
        feedback = ctx.session.state.get("judge_feedback")
        is_pass = False
        if isinstance(feedback, dict):
            if str(feedback.get("status", "")).lower() == "pass":
                is_pass = True

        if not is_pass:
            logger.error(
                "[ResearchGuard] Research failed to pass validation. Stopping pipeline."
            )
            yield Event(
                author=self.name,
                content=Content(
                    parts=[
                        Part(
                            text="ERROR: Research could not be completed successfully after multiple attempts. Please refine your topic and try again."
                        )
                    ]
                ),
            )
        else:
            logger.info("[ResearchGuard] Research validated. Proceeding.")
            topic = ctx.session.state.get("topic", "the requested topic")
            yield Event(author=self.name, content=Content(parts=[Part(text=topic)]))


root_agent = SequentialAgent(
    name="course_creation_pipeline",
    description="A pipeline that researches a topic and builds a course.",
    sub_agents=[
        ProgressAgent("🚀 Starting the course creation pipeline..."),
        TopicCapturer(name="capture_topic"),
        research_loop,
        ResearchGuard(name="research_guard"),
        ProgressAgent(
            "✍️ Building the final course content...", author="content_builder"
        ),
        StateCapturer(
            output_key="research_findings",
            restore_from_state=True,
            author_filter="researcher",
            prefix_with_topic=True,
        ),
        content_builder,
    ],
)

agent = root_agent
