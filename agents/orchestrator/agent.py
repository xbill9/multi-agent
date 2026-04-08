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

class StateCapturer(BaseAgent):
    """Captures the last text output from the session history into state."""
    
    _output_key: str = PrivateAttr()
    
    def __init__(self, output_key: str):
        super().__init__(name=f"capture_{output_key}")
        self._output_key = output_key

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event]:
        # Search backward for the last invocation that has text content
        text = ""
        
        if ctx.session.events:
            for event in reversed(ctx.session.events):
                # Ignore our own messages or empty messages
                if event.author == self.name:
                    continue
                
                # Ignore ProgressAgent messages (author names like 'progress_researcher')
                if "progress" in event.author.lower():
                    continue

                if event.content and event.content.parts:
                    invocation_text = ""
                    for part in event.content.parts:
                        if part.text:
                            # Also ignore text that looks like a progress message emoji-based
                            if part.text.strip().startswith(("🔍", "⚖️", "🚀", "✍️", "⌛")):
                                continue
                            invocation_text += part.text
                    
                    if not invocation_text.strip() and event.grounding_metadata:
                        # If no text but we have grounding metadata, let's capture that!
                        metadata = event.grounding_metadata
                        if hasattr(metadata, "web_search_queries") and metadata.web_search_queries:
                             invocation_text = f"The model performed these searches: {', '.join(metadata.web_search_queries)}"
                        if hasattr(metadata, "grounding_chunks") and metadata.grounding_chunks:
                             invocation_text += "\n\nGrounding sources found:\n"
                             for chunk in metadata.grounding_chunks:
                                 if hasattr(chunk, "web"):
                                     invocation_text += f"- {chunk.web.title}: {chunk.web.uri}\n"

                    if invocation_text.strip():
                        text = invocation_text
                        logger.info(f"[{self.name}] Found content from {event.author}")
                        break
        
        if text:
            # Try to parse as JSON if it looks like it
            if text.strip().startswith("{"):
                try:
                    ctx.session.state[self._output_key] = json.loads(text)
                except json.JSONDecodeError:
                    ctx.session.state[self._output_key] = text
            else:
                ctx.session.state[self._output_key] = text
            
            logger.info(f"[{self.name}] Captured content to state: {self._output_key}")
        else:
            logger.warning(f"[{self.name}] No content found to capture for {self._output_key}")
            
        # Return the captured text so it flows as the new user_content to the next agent
        yield Event(author=self.name, content=Content(parts=[Part(text=text)]))

class EscalationChecker(BaseAgent):
    """Checks the Judge's feedback in session state and signals loop termination."""

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event]:
        # Try finding feedback in multiple locations for robustness
        feedback = ctx.session.state.get("judge_feedback") or ctx.session.state.get("judge_evaluation")
        
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
            if '"status": "pass"' in feedback_lower or '"status":"pass"' in feedback_lower:
                is_pass = True
            elif "status" in feedback_lower and "pass" in feedback_lower:
                 import re
                 if re.search(r'"status"\s*:\s*"pass"', feedback_lower) or re.search(r"status\s*:\s*pass", feedback_lower):
                     is_pass = True

        if is_pass:
            logger.info("[EscalationChecker] Research approved. ESCALATING.")
            yield Event(
                author=self.name,
                actions=EventActions(escalate=True),
                content=Content(parts=[Part(text="Research approved. Moving to content builder.")])
            )
        else:
            logger.info("[EscalationChecker] Research needs refinement. CONTINUING LOOP.")
            yield Event(
                author=self.name,
                content=Content(parts=[Part(text="Research needs more work. Refining search...")])
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
        yield Event(
            author=self._author,
            content=Content(parts=[Part(text=self._message)])
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
    use_legacy=False,
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
    use_legacy=False,
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
    use_legacy=False,
)

# --- Orchestration ---

research_loop = LoopAgent(
    name="research_loop",
    description="Iteratively researches and judges findings.",
    sub_agents=[
        ProgressAgent("🔍 Research is starting...", author="researcher"),
        researcher,
        StateCapturer(output_key="research_findings"),
        ProgressAgent("⚖️ Judge is evaluating findings...", author="judge"),
        judge,
        StateCapturer(output_key="judge_feedback"),
        EscalationChecker(name="escalation_checker")
    ],
    max_iterations=2,
)

root_agent = SequentialAgent(
    name="course_creation_pipeline",
    description="A pipeline that researches a topic and builds a course.",
    sub_agents=[
        ProgressAgent("🚀 Starting the course creation pipeline..."),
        research_loop, 
        ProgressAgent("✍️ Building the final course content...", author="content_builder"),
        content_builder
    ],
)

agent = root_agent
