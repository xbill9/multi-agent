# Makefile for Orchestrator Agent

SHELL := /bin/bash
PYTHON = python3
PIP = pip3
PORT = 8080

# Find the project root directory
PROJECT_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || pwd)
export PROJECT_ROOT

# Load .env file if it exists
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

# Deployment variables
REGION ?= us-central1
GOOGLE_CLOUD_PROJECT ?= $(shell gcloud config get-value project)
GENAI_MODEL ?= gemini-2.5-flash
SERVICE_URL ?= $(shell gcloud run services describe orchestrator --region $(REGION) --format='value(status.url)' --project $(GOOGLE_CLOUD_PROJECT) 2>/dev/null)
AGENT_NAME ?= orchestrator
TOPIC ?= The impact of AI on software engineering

.PHONY: all help install run start stop status lint format test deploy clean a2a test-invoke test-local endpoint check-env

# Default target
all: run

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

status:
	@echo "--- Local Status (Port $(PORT)) ---"
	@if lsof -Pi :$(PORT) -sTCP:LISTEN -t >/dev/null; then \
		echo "Agent is RUNNING on port $(PORT)"; \
	else \
		echo "Agent is NOT RUNNING locally"; \
	fi
	@echo "--- Cloud Run Status ($(AGENT_NAME)) ---"
	@if [ -n "$(SERVICE_URL)" ]; then \
		echo "Service is DEPLOYED at $(SERVICE_URL)"; \
	else \
		echo "Service is NOT DEPLOYED to Cloud Run"; \
	fi

# Install dependencies
install:
	$(PIP) install -e .

# Run the orchestrator agent
run: check-env
	./run.sh

start: check-env
	@if lsof -Pi :$(PORT) -sTCP:LISTEN -t >/dev/null; then \
		echo "Agent is already running on port $(PORT)"; \
	else \
		echo "Starting agent on port $(PORT)..."; \
		nohup ./run.sh > agent.log 2>&1 & echo $$! > agent.pid; \
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

# Deploy to Cloud Run using Cloud Build
deploy: check-env
	@echo "Deploying orchestrator agent to Cloud Run using cloudbuild.yaml..."
	@echo "Building from project root: $(PROJECT_ROOT)"
	gcloud builds submit $(PROJECT_ROOT) \
		--project $(GOOGLE_CLOUD_PROJECT) \
		--config cloudbuild.yaml \
		--substitutions=_REGION=$(REGION),_GENAI_MODEL=$(GENAI_MODEL),_GOOGLE_API_KEY=$(GOOGLE_API_KEY)

# Get the deployed service URL
endpoint:
	@if [ -z "$(SERVICE_URL)" ]; then \
		echo "Error: Could not determine SERVICE_URL. Ensure the service '$(AGENT_NAME)' is deployed in project '$(GOOGLE_CLOUD_PROJECT)' and region '$(REGION)'."; \
		exit 1; \
	fi
	@echo $(SERVICE_URL)

# Get the A2A Agent Card
a2a:
	@if [ -z "$(SERVICE_URL)" ]; then echo "Error: SERVICE_URL is not set. Deploy the agent first or provide SERVICE_URL=..."; exit 1; fi
	@echo "Fetching Agent Card for '$(AGENT_NAME)' from $(SERVICE_URL)..."
	@curl -s $(SERVICE_URL)/a2a/$(AGENT_NAME)/.well-known/agent-card.json | jq .

# Run tests
test: check-env
	PYTHONPATH=../.. $(PYTHON) -m pytest test_orchestrator.py

# Lint the code using ruff
lint:
	ruff check .

# Format the code using ruff
format:
	ruff format .
	ruff check . --fix

# Clean up temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.log" -exec rm -rf {} +
	rm -rf .adk/artifacts
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .adk/session.db
	rm -rf *.egg-info

test-invoke:
	@URL=$(if $(SERVICE_URL),$(SERVICE_URL),http://localhost:$(PORT)); \
	echo "Testing endpoint at $$URL/a2a/$(AGENT_NAME) with topic: '$(TOPIC)'..."; \
	curl -s -X POST $$URL/a2a/$(AGENT_NAME) \
	  -H "Content-Type: application/json" \
	  -d '{"jsonrpc": "2.0", "id": "1", "method": "message/send", "params": {"contextId": "test-session", "message": {"role": "user", "parts": [{"text": "$(TOPIC)"}], "messageId": "m1"}}}' | jq .

test-local:
	@echo "Testing local endpoint at http://localhost:$(PORT)/a2a/$(AGENT_NAME) with topic: '$(TOPIC)'..."; \
	curl -s -X POST http://localhost:$(PORT)/a2a/$(AGENT_NAME) \
	  -H "Content-Type: application/json" \
	  -d '{"jsonrpc": "2.0", "id": "1", "method": "message/send", "params": {"contextId": "test-session", "message": {"role": "user", "parts": [{"text": "$(TOPIC)"}], "messageId": "m1"}}}' | jq .
