# Makefile for Judge Agent

PYTHON = python3
PIP = pip3
PORT = 8002

# Find the project root directory
PROJECT_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || pwd)
export PROJECT_ROOT

.PHONY: help install run lint test clean deploy endpoint a2a test-invoke logs status

help:
	@echo "Available targets:"
	@echo "  install  - Install dependencies"
	@echo "  run      - Run the agent locally on port $(PORT)"
	@echo "  status   - Check local and remote service status"
	@echo "  lint     - Run linting (ruff)"
	@echo "  test     - Run tests (pytest)"
	@echo "  clean    - Remove temporary files and cache"
	@echo "  deploy   - Deploy to Google Cloud Run"
	@echo "  endpoint - Show the deployed service URL"
	@echo "  a2a      - Fetch the A2A Agent Card"
	@echo "  test-invoke - Test agent invocation via A2A"
	@echo "  logs     - Show Cloud Run logs"

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

install:
	$(PIP) install -e .

run:
	$(PYTHON) -m shared.adk_app --port $(PORT) --a2a

lint:
	ruff check .

test:
	pytest

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .adk/artifacts
	rm -rf .pytest_cache
	rm -rf .ruff_cache

# Deployment Configuration
# Usage: make deploy GOOGLE_CLOUD_PROJECT=your-project REGION=us-central1
GOOGLE_CLOUD_PROJECT ?= $(shell gcloud config get-value project)
REGION ?= us-central1
GENAI_MODEL ?= gemini-2.5-flash
# GOOGLE_API_KEY should be set in your environment

# A2A Configuration
SERVICE_URL ?= $(shell gcloud run services describe judge --platform managed --region $(REGION) --project $(GOOGLE_CLOUD_PROJECT) --format 'value(status.url)' 2>/dev/null)
AGENT_NAME ?= judge

deploy:
	@echo "Deploying judge agent to Cloud Run..."
	gcloud run deploy judge \
		--source . \
		--project $(GOOGLE_CLOUD_PROJECT) \
		--region $(REGION) \
		--allow-unauthenticated \
		--set-env-vars GOOGLE_CLOUD_PROJECT="$(GOOGLE_CLOUD_PROJECT)",GOOGLE_GENAI_USE_VERTEXAI="false",GOOGLE_API_KEY="$(GOOGLE_API_KEY)",GENAI_MODEL="$(GENAI_MODEL)"

endpoint:
	@if [ -z "$(SERVICE_URL)" ]; then echo "Error: SERVICE_URL is not set. Deploy the agent first."; exit 1; fi
	@echo "$(SERVICE_URL)"

a2a:
	@if [ -z "$(SERVICE_URL)" ]; then echo "Error: SERVICE_URL is not set. Deploy the agent first or provide SERVICE_URL=..."; exit 1; fi
	@echo "Fetching Agent Card for '$(AGENT_NAME)' from $(SERVICE_URL)..."
	curl -s $(SERVICE_URL)/a2a/$(AGENT_NAME)/.well-known/agent-card.json | jq .

test-invoke:
	@if [ -z "$(SERVICE_URL)" ]; then echo "Error: SERVICE_URL is not set. Deploy the agent first or provide SERVICE_URL=..."; exit 1; fi
	$(PYTHON) tests/invoke_agent.py "$(SERVICE_URL)" "$(AGENT_NAME)" "$(INPUT_TEXT)"

logs:
	gcloud run services logs read judge --project $(GOOGLE_CLOUD_PROJECT) --region $(REGION) --limit 50
