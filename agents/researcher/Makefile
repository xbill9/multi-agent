# Makefile for Researcher Agent

SHELL := /bin/bash
PYTHON = python3
PIP = pip3
PORT = 8001

# Find the project root directory
PROJECT_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || pwd)
export PROJECT_ROOT

# Load .env file if it exists
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

.PHONY: help install run start stop lint format test deploy clean a2a test-invoke test-local endpoint status check-env

check-env:
	@if [ -z "$(GOOGLE_API_KEY)" ]; then \
		echo "Error: GOOGLE_API_KEY is not set. Please set it in .env or as an environment variable"; \
		exit 1; \
	fi

help:
	@echo "Available targets:"
	@echo "  install      - Install dependencies"
	@echo "  run          - Run the agent locally on port $(PORT)"
	@echo "  start        - Start the agent in background"
	@echo "  stop         - Stop the local agent"
	@echo "  status       - Check local and remote service status"
	@echo "  lint         - Run linting (ruff)"
	@echo "  format       - Run formatting (ruff format)"
	@echo "  test         - Run tests (pytest)"
	@echo "  a2a          - Fetch the A2A Agent Card"
	@echo "  test-invoke  - Test the agent endpoint with a research TOPIC (prefers Cloud Run if deployed)"
	@echo "  test-local   - Test the local agent endpoint with a research TOPIC"
	@echo "  clean        - Remove temporary files and cache"
	@echo "  deploy       - Deploy to Google Cloud Run"
	@echo "  endpoint     - Get the deployed service URL"

install:
	$(PIP) install -e .

run: check-env
	$(PYTHON) -m shared.adk_app --port $(PORT) --a2a

start: check-env
	@if lsof -Pi :$(PORT) -sTCP:LISTEN -t >/dev/null; then \
		echo "Agent is already running on port $(PORT)"; \
	else \
		echo "Starting agent on port $(PORT)..."; \
		nohup $(PYTHON) -m shared.adk_app --port $(PORT) --a2a > agent.log 2>&1 & echo $$! > agent.pid; \
		echo "Agent started with PID $$(cat agent.pid). Logging to agent.log"; \
	fi

stop:
	@echo "Stopping agent on port $(PORT)..."
	@if [ -f agent.pid ]; then \
		kill $$(cat agent.pid) && rm agent.pid; \
		echo "Agent stopped."; \
	elif lsof -Pi :$(PORT) -sTCP:LISTEN -t >/dev/null; then \
		lsof -Pi :$(PORT) -sTCP:LISTEN -t | xargs kill; \
		echo "Agent stopped."; \
	else \
		echo "Agent is not running."; \
	fi

lint:
	ruff check .

format:
	ruff format .
	ruff check . --fix

test: check-env
	$(PYTHON) -m pytest -W "ignore:[EXPERIMENTAL] feature FeatureName.PLUGGABLE_AUTH is enabled:UserWarning"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.log" -exec rm -rf {} +
	rm -rf .adk/artifacts
	rm -rf .pytest_cache
	rm -rf .ruff_cache

# A2A Configuration
GENAI_MODEL ?= gemini-2.5-flash
AGENT_NAME ?= researcher
TOPIC ?= The impact of AI on software engineering

a2a:
	@if [ -z "$(SERVICE_URL)" ]; then echo "Error: SERVICE_URL is not set. Deploy the agent first or provide SERVICE_URL=..."; exit 1; fi
	@echo "Fetching Agent Card for '$(AGENT_NAME)' from $(SERVICE_URL)..."
	curl -s $(SERVICE_URL)/a2a/$(AGENT_NAME)/.well-known/agent-card.json | jq .

test-local:
	@echo "Testing local endpoint at http://localhost:$(PORT)/a2a/$(AGENT_NAME) with topic: '$(TOPIC)'..."; \
	curl -s -X POST http://localhost:$(PORT)/a2a/$(AGENT_NAME) \
	  -H "Content-Type: application/json" \
	  -d '{"jsonrpc": "2.0", "id": "1", "method": "message/send", "params": {"contextId": "test-session", "message": {"role": "user", "parts": [{"text": "$(TOPIC)"}], "messageId": "m1"}}}' | jq .

