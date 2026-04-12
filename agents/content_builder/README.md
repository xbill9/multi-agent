# Content Builder Agent

The Content Builder is a specialized microservice agent designed to transform raw research findings into structured, high-quality course modules in Markdown format. It is part of the AI Course Creator multi-agent system.

## Overview

This agent takes a target topic and research findings as input and generates a comprehensive educational document. It leverages the Google Agent Development Kit (ADK) and the A2A (Agent-to-Agent) protocol for seamless integration within a distributed system.

### Key Responsibilities

- **Structured Formatting:** Uses H1 for titles, H2 for main modules, and H3 for sub-sections.
- **Content Integrity:** Ensures accurate and easy-to-read output without introductory meta-commentary.
- **Topic Recovery:** Implements heuristics to identify the target topic and findings from session history if they are not explicitly present in the state.

## Technical Details

- **Model:** Default is `gemini-2.5-flash` (configurable via `GENAI_MODEL`).
- **Framework:** Built with [Google ADK](https://github.com/google/adk).
- **Transport:** Uses JSONRPC over HTTP (A2A Protocol).
- **Logging:** Centralized JSON logging via `shared.logging_config`.

## Getting Started

### Prerequisites

- Python 3.13+
- A Google API Key with access to Gemini models.

### Installation

```bash
make install
```

### Configuration

Create a `.env` file or set the following environment variables:

- `GOOGLE_API_KEY` (or `GEMINI_API_KEY`): Your Google AI API key.
- `GENAI_MODEL`: (Optional) The model to use (default: `gemini-2.5-flash`).

### Running Locally

```bash
make run
```
The agent will start on port `8003` by default.

### Testing and Quality Control

- **Run Tests:** `make test`
- **Linting:** `make lint`
- **Formatting:** `make format`

## Deployment


```bash
make deploy
```


## API Specification

The agent implements the A2A protocol. It expects a message containing the target topic and research findings, either via the session state or directly in the message parts.

### Input State Variables
- `topic`: The subject of the course.
- `research_findings`: The raw data gathered by the Researcher agent.

### Output
A single, clean Markdown document starting with the Course Title (#).
