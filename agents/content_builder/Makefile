# Makefile for Content Builder Agent

SHELL := /bin/bash
PYTHON = python3
PIP = pip3
PORT = 8003
SERVICE_NAME = content-builder
AGENT_NAME = content_builder
GENAI_MODEL ?= gemini-2.5-flash

# Find the project root directory
PROJECT_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || pwd)
export PROJECT_ROOT

# Load .env file if it exists
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

# Support both GOOGLE_API_KEY and GEMINI_API_KEY
GOOGLE_API_KEY ?= $(GEMINI_API_KEY)
export GOOGLE_API_KEY

TOPIC ?= Please generate a course module based on these findings.
RESEARCH_FINDINGS ?= The Gemini 2.5 models are the latest from Google. They offer improved reasoning and speed. Key features include large context windows and native multimodal capabilities.

.PHONY: help install run start stop lint format test clean build deploy a2a endpoint test-invoke status test-local

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
	@echo "  clean        - Remove temporary files and cache"
	@echo "  build        - Build and deploy using Cloud Build"
	@echo "  deploy       - Deploy to Cloud Run"
	@echo "  endpoint     - Get the Cloud Run service URL"
	@echo "  a2a          - Fetch the A2A agent card (uses SERVICE_URL if set/found, else localhost)"
	@echo "  test-invoke  - Call the agent endpoint with a research TOPIC and RESEARCH_FINDINGS"
	@echo "  test-local   - Test the local agent endpoint with a research TOPIC and RESEARCH_FINDINGS"

install:
	$(PIP) install -e .

run:
	$(PYTHON) -m shared.adk_app .. --port $(PORT) --a2a

start:
	@if lsof -Pi :$(PORT) -sTCP:LISTEN -t >/dev/null; then \
		echo "Agent is already running on port $(PORT)"; \
	else \
		echo "Starting agent on port $(PORT)..."; \
		nohup $(PYTHON) -m shared.adk_app .. --port $(PORT) --a2a > agent.log 2>&1 & echo $$! > agent.pid; \
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

test:
	$(PYTHON) -m pytest -W "ignore:[EXPERIMENTAL] feature FeatureName.PLUGGABLE_AUTH is enabled:UserWarning"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.log" -exec rm -rf {} +
	rm -rf .adk/artifacts
	rm -rf .pytest_cache
	rm -rf .ruff_cache

a2a:
	@if [ -n "$(SERVICE_URL)" ]; then \
		echo "Fetching agent card from $(SERVICE_URL)..."; \
		curl -s $(SERVICE_URL)/a2a/$(AGENT_NAME)/.well-known/agent-card.json | jq .; \
	else \
		echo "SERVICE_URL not found, fetching from localhost:$(PORT)..."; \
		curl -s http://localhost:$(PORT)/a2a/$(AGENT_NAME)/.well-known/agent-card.json | jq .; \
	fi

test-local:
	@echo "Testing local endpoint at http://localhost:$(PORT)/a2a/$(AGENT_NAME) with findings and topic..."; \
	curl -s -X POST http://localhost:$(PORT)/a2a/$(AGENT_NAME) \
	  -H "Content-Type: application/json" \
	  -d '{"jsonrpc": "2.0", "id": "1", "method": "message/send", "params": {"contextId": "test-session", "message": {"role": "user", "parts": [{"text": "RESEARCH FINDINGS:\n$(RESEARCH_FINDINGS)\n\nUSER QUERY:\n$(TOPIC)"}], "messageId": "m1"}}}' | jq .
