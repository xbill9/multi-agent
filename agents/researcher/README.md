# Researcher Agent

The **Researcher Agent** is a specialized microservice designed to gather comprehensive information on a given topic using real-time search capabilities. It is built using the Google Agent Development Kit (ADK) and follows the Agent-to-Agent (A2A) protocol for seamless integration into multi-agent systems.

## Features

- **Real-time Research**: Equipped with the `google_search` tool to fetch up-to-date information from the web.
- **Detailed Reporting**: Generates structured Markdown reports including history, key figures, and impact.
- **Citations & Sources**: Always provides source URLs or titles for transparency and verification.
- **Adaptive Search**: Can refine its search queries based on feedback from other agents (e.g., a Judge agent).
- **Standardized Logging**: Integrated with structured JSON logging for observability.

## Technical Stack

- **Framework**: Google Agent Development Kit (ADK)
- **Model**: `gemini-2.5-flash` (recommended for speed and efficiency)
- **Protocol**: A2A (Agent-to-Agent)
- **Runtime**: Python 3.13+

## Getting Started

### Prerequisites

- Python 3.13+
- A Google Cloud Project with the Generative AI API enabled.
- A valid `GOOGLE_API_KEY` or configured Google Cloud credentials.

### Installation

1. Install the dependencies:
   ```bash
   make install
   ```

2. Configure your environment by creating a `.env` file:
   ```env
   GOOGLE_API_KEY=your_api_key_here
   GENAI_MODEL=gemini-2.5-flash
   ```

### Running Locally

To start the agent on the default port (8001):
```bash
make run
```

## Development & Testing

### Available Commands

- `make test`: Run unit tests using `pytest`.
- `make lint`: Run linting checks using `ruff`.
- `make format`: Format code using `ruff`.
- `make clean`: Remove temporary files and cache.

### Testing the Endpoint

You can test the agent's research capabilities using the `test-invoke` target:
```bash
make test-invoke TOPIC="The impact of AI on software engineering"
```

## Deployment

```bash
make deploy
```

## Agent Card (A2A)

When running, the agent exposes its A2A Agent Card at:
`http://localhost:8001/a2a/researcher/.well-known/agent-card.json`
