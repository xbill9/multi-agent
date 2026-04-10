# AI Course Creator (Distributed Multi-Agent System)

A multi-agent system built with Google's Agent Development Kit (ADK) and Agent-to-Agent (A2A) protocol. It features a team of specialized microservice agents that research, judge, and build content, orchestrated to deliver high-quality educational modules.

## Architecture

This project uses a distributed microservices architecture where each agent runs in its own container and communicates via the A2A protocol:

*   **Orchestrator Service (`agents/orchestrator`):** Manages the overall course creation pipeline using **`SequentialAgent`**. It implements an iterative Research-Judge loop with **`LoopAgent`** (max 2 iterations). Key components include **`TopicCapturer`**, **`EscalationChecker`**, **`ResearchGuard`**, **`StateCapturer`**, and **`ProgressAgent`** for status updates.
*   **Researcher Service (`agents/researcher`):** Gathers detailed topic information using the `google_search` tool.
*   **Judge Service (`agents/judge`):** Evaluates research quality against a Pydantic schema (`JudgeFeedback`).
*   **Content Builder Service (`agents/content_builder`):** Compiles validated research into a professional Markdown course module.
*   **Web App (`app/`):** A FastAPI backend with a Vanilla TypeScript + Vite frontend that streams real-time agent events via SSE.

## Project Structure

```
multi-agent/
├── agents/
│   ├── orchestrator/     # Workflow management & remote agent connections
│   ├── researcher/       # Information gathering (Google Search)
│   ├── judge/            # Quality control (Structured Feedback)
│   └── content_builder/  # Content generation (Markdown)
├── app/                  # Web application (FastAPI + Vanilla TS Frontend)
├── shared/               # Shared utilities (Symlinked into agents)
│   ├── a2a_utils.py      # A2A URL rewriting middleware
│   ├── adk_app.py        # Standardized ADK FastAPI wrapper
│   ├── authenticated_httpx.py # Service-to-service auth utilities
│   └── logging_config.py # Centralized logging configuration
├── Makefile              # Development shortcuts
├── run_local.sh          # Local development startup script
├── deploy.sh             # Cloud Run deployment script
├── init.sh               # Project creation and billing setup script
├── init2.sh              # Service enablement and environment initialization
├── set_adc.sh            # GCloud Application Default Credentials setup
├── set_env.sh            # Local .env generation script
└── *_test.sh             # Agent-specific testing scripts
```

## Requirements

*   **Python 3.13+**
*   **Node.js & npm**: For frontend development and builds.
*   **pip** or **uv**: For dependency management.
*   **Google Cloud SDK**: For authentication and deployment.
*   **Google API Key**: Required for Gemini (unless using Vertex AI).

## Quick Start

1.  **Initialize Environment:**
    ```bash
    # Create project and enable billing (if needed)
    ./init.sh
    # Enable services and set up .env
    ./init2.sh
    ```

2.  **Install Dependencies:**
    ```bash
    # This installs root, agents, app, and frontend dependencies
    make install
    
    # Optional: using uv
    uv sync
    ```

3.  **Run Locally:**
    ```bash
    ./run_local.sh
    ```
    This starts all agents and the web app. The Researcher, Judge, and Content Builder run on ports 8001-8003, the Orchestrator on 8004, and the Web App on 8000.

4.  **Access the App:**
    -   **http://localhost:8000**: Main entry point (FastAPI serving the built frontend).
    -   **http://localhost:5173**: Vite dev server (supports hot-reloading for UI development).

## Testing

Run agent-specific tests to verify individual components:
```bash
./research_test.sh
./judge_test.sh
```
Or run the full suite:
```bash
make test
```

### Direct Agent Testing
You can test an agent directly without the A2A protocol using a Python script. This is useful for debugging:
```bash
python test_researcher_direct.py
```

## Deployment

The system is designed to be deployed to **Google Cloud Run**.

1.  **Configure Environment:**
    Set `GOOGLE_API_KEY` or ensure Vertex AI is enabled.
    Set `GENAI_MODEL` to `gemini-2.5-flash` (recommended).

2.  **Run Deployment Script:**
    ```bash
    ./deploy.sh
    ```

## Recommended Models

*   **Primary:** `gemini-2.5-flash` (Recommended) for superior reasoning, tool-calling accuracy, and cost-effectiveness.
*   **Alternative:** `gemini-2.5-pro` for tasks requiring even deeper reasoning or complex instruction following.
*   **Note:** Do not use models less than 2.5 (e.g., 2.0 Flash) as they are deprecated.
