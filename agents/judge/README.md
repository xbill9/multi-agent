# Judge Agent

The Judge Agent is a specialized quality controller microservice designed to evaluate research findings for accuracy, completeness, and structure. It is part of a distributed multi-agent system and is built using the Google Agent Development Kit (ADK).

## Key Features

- **Quality Evaluation**: Assesses research based on Accuracy, Completeness, Structure, and Source Variety.
- **Structured Feedback**: Returns evaluation results via a Pydantic `JudgeFeedback` schema (`status: pass/fail`, `feedback: str`).
- **Research Recovery**: Intelligently identifies and extracts research findings from the session history or state.
- **A2A Support**: Fully compatible with the Agent-to-Agent (A2A) protocol for distributed multi-agent communication.

## Configuration

- **Model**: `gemini-2.5-flash` (configurable via `GENAI_MODEL` environment variable).
- **Port**: `8002` (default local development port).

## Development and Deployment

The included `Makefile` provides targets for common tasks:

- `make install`: Install dependencies locally.
- `make run`: Run the agent locally on port 8002 (requires `GOOGLE_API_KEY`).
- `make start`: Start the agent in the background.
- `make test`: Run the test suite using `pytest`.
- `make lint`: Run code linting with `ruff`.
- `make format`: Format code with `ruff`.

## API Integration

The agent exposes a JSON-RPC interface via the A2A protocol. It expects research findings as input and provides a structured evaluation as output.

### Evaluation Criteria
1. **Accuracy**: Are the facts presented correct and verifiable?
2. **Completeness**: Does the research cover all key aspects of the requested topic?
3. **Structure**: Is the information organized logically for a course module?
4. **Source Variety**: Does the research draw from multiple reliable sources (if applicable)?
