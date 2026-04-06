# ADK & Gemini 2.5 Pro Course Creation Guide

This document provides technical guidance for developers working with the Google Agent Development Kit (ADK) and the Gemini 2.5 Pro model within the **AI Course Creator** project.

## Project Overview: AI Course Creator

The AI Course Creator is a distributed multi-agent system designed to autonomously research topics and generate structured course modules. It leverages the **Agent-to-Agent (A2A)** protocol to enable communication between specialized microservice agents.

### Key Architectural Components

1.  **Orchestrator (`agents/orchestrator`):**
    *   Uses `SequentialAgent` to define a high-level pipeline.
    *   Uses `LoopAgent` to implement an iterative Research-Judge feedback loop.
    *   Employs `RemoteA2aAgent` to connect to distributed services over HTTP.
2.  **Researcher (`agents/researcher`):**
    *   Powered by `gemini-2.5-pro`.
    *   Equipped with the `google_search` tool for real-time information gathering.
3.  **Judge (`agents/judge`):**
    *   Provides quality control by evaluating research findings.
    *   Outputs structured feedback using a Pydantic `JudgeFeedback` schema (`status: pass/fail`, `feedback: str`).
4.  **Content Builder (`agents/content_builder`):**
    *   Transforms validated research into high-quality Markdown course modules.
5.  **Web App (`app`):**
    *   A FastAPI backend that streams agent events to a React frontend using Server-Sent Events (SSE).

## Working with ADK & A2A

### Distributed Agent Communication (A2A)

Each agent in this system is an independent ADK service. They communicate using the A2A protocol, which involves:
-   **Agent Cards**: Each service exposes an `agent-card.json` (at `.well-known/agent-card.json`) describing its capabilities.
-   **Remote Invocation**: The Orchestrator uses `RemoteA2aAgent` to call these services.
-   **URL Rewriting**: For Cloud Run deployments, `shared/a2a_utils.py` is used to dynamically update agent URLs in the cards.

### Shared Utilities & Symlinks

To ensure consistency and avoid code duplication, core logic is stored in the `shared/` directory and symlinked into each agent's folder:
-   `adk_app.py`: Standardized FastAPI wrapper for ADK agents.
-   `authenticated_httpx.py`: Handles secure service-to-service authentication in GCP.
-   `a2a_utils.py`: Utilities for managing A2A discovery and communication.

## Model Selection & Optimization

*   **Primary Model:** `gemini-2.5-pro` is recommended for all agents due to its superior reasoning, tool-calling accuracy, and support for complex orchestration.
*   **Structured Output:** Always use Pydantic schemas (like `JudgeFeedback`) for agents that provide evaluation or data that must be parsed programmatically (e.g., by the `EscalationChecker`).
*   **Context Management:** Use `LoopAgent`'s `max_iterations` to prevent infinite loops during the research phase.

## Developer Workflow

1.  **Local Development:** Use `./run_local.sh` (or `make run`) to start the entire stack on ports 8000-8004.
2.  **Adding Tools:** New tools should be added to the `tools` list in the respective agent's `agent.py` file.
3.  **Refining Instructions:** Modify the `instruction` string in each agent's definition to tune their persona and output quality.
4.  **Testing:** Run `make test` to execute the full suite of backend and integration tests.

## Resources

-   [Google ADK Documentation](https://github.com/google/adk)
-   [Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
-   [A2A Protocol Specification](https://github.com/google/adk/blob/main/docs/a2a.md)
