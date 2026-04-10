# Orchestrator Agent

The **Orchestrator Agent** is the central brain of the AI Course Creator system. It implements a sophisticated multi-agent pipeline using the [Agent Developer Kit (ADK)](https://github.com/google/adk) to autonomously research topics and generate structured course content.

## Overview

This agent coordinates the work of three specialized sub-agents:
1.  **Researcher**: Gathers information using Google Search.
2.  **Judge**: Evaluates the quality and completeness of the research.
3.  **Content Builder**: Transforms the validated research into a high-quality Markdown course.

## Workflow

The orchestrator follows a strict sequential pipeline:

1.  **Topic Capture**: Extracts the research topic from the user's initial message and cleans it for the sub-agents.
2.  **Research-Judge Loop**:
    -   Triggers the **Researcher** to gather data.
    -   Triggers the **Judge** to evaluate the findings.
    -   If the Judge passes the research, the loop terminates early (**Escalation**).
    -   If the Judge fails the research, it repeats (up to 2 iterations) to refine the findings.
3.  **Research Guard**: A safety gate that ensures the research meets quality standards before proceeding to generation.
4.  **Content Generation**: Passes the final, validated research to the **Content Builder** to create the course modules.

Throughout the process, the orchestrator sends **Progress Events** (`progress_orchestrator`, `progress_researcher`, etc.) to provide real-time feedback to the user interface.

## Technical Architecture

-   **Base Framework**: Google ADK (`SequentialAgent`, `LoopAgent`, `BaseAgent`).
-   **Communication**: Uses the **A2A (Agent-to-Agent)** protocol for secure, authenticated communication between microservices.
-   **State Management**: Utilizes the ADK `session.state` to persist findings and feedback across different pipeline stages.
-   **Service Discovery**: Dynamically resolves sub-agent URLs via environment variables or falls back to local defaults.

## Key Components

-   `TopicCapturer`: Extracts the core topic from messy user input.
-   `StateCapturer`: A utility agent that "scrapes" history and persists specific outputs into the session state.
-   `EscalationChecker`: Evaluates structured JSON feedback from the Judge to decide whether to continue the research loop.
-   `ResearchGuard`: Prevents the system from attempting to build a course on failed or insufficient research.

## Getting Started

### Prerequisites

-   Python 3.10+
-   Access to Google Cloud (for Gemini models and deployment)
-   `GOOGLE_API_KEY` set in your environment or `.env` file.

### Installation

```bash
make install
```

### Running Locally

```bash
make run
```
The agent will start on port `8080` (by default).

### Testing

```bash
make test
```

## Environment Variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| `RESEARCHER_AGENT_CARD_URL` | A2A URL for the Researcher agent. | `http://localhost:8001/...` |
| `JUDGE_AGENT_CARD_URL` | A2A URL for the Judge agent. | `http://localhost:8002/...` |
| `CONTENT_BUILDER_AGENT_CARD_URL` | A2A URL for the Content Builder agent. | `http://localhost:8003/...` |
| `GENAI_MODEL` | The Gemini model to use. | `gemini-2.5-flash` |
| `GOOGLE_API_KEY` | Your Google AI Studio API Key. | (Required) |
