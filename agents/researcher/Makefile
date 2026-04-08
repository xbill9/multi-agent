# Makefile for Researcher Agent

PYTHON = python3
PIP = pip3
PORT = 8001

# Find the project root directory
PROJECT_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || pwd)
export PROJECT_ROOT

.PHONY: help install run lint format test deploy clean a2a test-invoke endpoint status

help:
	@echo "Available targets:"
	@echo "  install  - Install dependencies"
	@echo "  run      - Run the agent locally on port $(PORT)"
	@echo "  status   - Check local and remote service status"
	@echo "  lint     - Run linting (ruff)"
	@echo "  format   - Run formatting (ruff format)"
	@echo "  test     - Run tests (pytest)"
	@echo "  a2a      - Fetch the A2A Agent Card"
	@echo "  test-invoke - Test the agent endpoint with a research TOPIC"
	@echo "  clean    - Remove temporary files and cache"
	@echo "  deploy   - Deploy to Google Cloud Run"
	@echo "  endpoint - Get the deployed service URL"

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

format:
	ruff format .
	ruff check . --fix

test:
	pytest

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .adk/artifacts
	rm -rf .pytest_cache
	rm -rf .ruff_cache

# A2A Configuration
GOOGLE_CLOUD_PROJECT ?= $(shell gcloud config get-value project 2>/dev/null)
REGION ?= us-central1
GENAI_MODEL ?= gemini-2.5-flash
SERVICE_URL ?= $(shell gcloud run services describe researcher --platform managed --region $(REGION) --project $(GOOGLE_CLOUD_PROJECT) --format 'value(status.url)' 2>/dev/null)
AGENT_NAME ?= researcher
TOPIC ?= The impact of AI on software engineering

deploy:
	@echo "Deploying researcher agent to Cloud Run..."
	gcloud run deploy researcher \
		--source . \
		--project $(GOOGLE_CLOUD_PROJECT) \
		--region $(REGION) \
		--allow-unauthenticated \
		--set-env-vars GOOGLE_CLOUD_PROJECT="$(GOOGLE_CLOUD_PROJECT)",GOOGLE_GENAI_USE_VERTEXAI="false",GOOGLE_API_KEY="$(GOOGLE_API_KEY)",GENAI_MODEL="$(GENAI_MODEL)"

a2a:
	@if [ -z "$(SERVICE_URL)" ]; then echo "Error: SERVICE_URL is not set. Deploy the agent first or provide SERVICE_URL=..."; exit 1; fi
	@echo "Fetching Agent Card for '$(AGENT_NAME)' from $(SERVICE_URL)..."
	curl -s $(SERVICE_URL)/a2a/$(AGENT_NAME)/.well-known/agent-card.json | jq .

test-invoke:
	@URL=$(if $(SERVICE_URL),$(SERVICE_URL),http://localhost:$(PORT)); \
	echo "Testing endpoint at $$URL/a2a/$(AGENT_NAME) with topic: '$(TOPIC)'..."; \
	curl -s -X POST $$URL/a2a/$(AGENT_NAME) \
	  -H "Content-Type: application/json" \
	  -d '{"jsonrpc": "2.0", "id": "1", "method": "message/send", "params": {"contextId": "test-session", "message": {"role": "user", "parts": [{"text": "$(TOPIC)"}], "messageId": "m1"}}}' | jq .

endpoint:
	@if [ -z "$(SERVICE_URL)" ]; then \
		echo "Error: Could not determine SERVICE_URL. Ensure the service 'researcher' is deployed in project '$(GOOGLE_CLOUD_PROJECT)' and region '$(REGION)'."; \
		exit 1; \
	fi
	@echo $(SERVICE_URL)
