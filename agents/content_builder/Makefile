# Makefile for Content Builder Agent

PYTHON = python3
PIP = pip3
PORT = 8003
SERVICE_NAME = content-builder
AGENT_NAME = content_builder
REGION ?= us-central1
GOOGLE_CLOUD_PROJECT ?= $(shell gcloud config get-value project)
GENAI_MODEL ?= gemini-2.5-flash
SERVICE_URL ?= $(shell gcloud run services describe $(SERVICE_NAME) --region $(REGION) --format 'value(status.url)' 2>/dev/null)

# Find the project root directory
PROJECT_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || pwd)
export PROJECT_ROOT

TOPIC ?= Please generate a course module based on these findings.
RESEARCH_FINDINGS ?= The Gemini 2.5 models are the latest from Google. They offer improved reasoning and speed. Key features include large context windows and native multimodal capabilities.

.PHONY: help install run lint test clean deploy a2a endpoint test-invoke

help:
	@echo "Available targets:"
	@echo "  install  - Install dependencies"
	@echo "  run      - Run the agent locally on port $(PORT)"
	@echo "  lint     - Run linting (ruff)"
	@echo "  test     - Run tests (pytest)"
	@echo "  clean    - Remove temporary files and cache"
	@echo "  deploy   - Deploy to Cloud Run"
	@echo "  endpoint - Get the Cloud Run service URL"
	@echo "  a2a      - Fetch the A2A agent card (uses SERVICE_URL if set/found, else localhost)"
	@echo "  test-invoke - Call the agent endpoint with a research TOPIC and RESEARCH_FINDINGS"

install:
	$(PIP) install -e .

run:
	$(PYTHON) -m shared.adk_app .. --port $(PORT) --a2a

lint:
	ruff check .

test:
	pytest

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .adk/artifacts
	rm -rf .pytest_cache
	rm -rf .ruff_cache

deploy:
	gcloud run deploy $(SERVICE_NAME) \
		--source . \
		--project $(GOOGLE_CLOUD_PROJECT) \
		--region $(REGION) \
		--allow-unauthenticated \
		--set-env-vars GOOGLE_CLOUD_PROJECT=$(GOOGLE_CLOUD_PROJECT) \
		--set-env-vars GOOGLE_GENAI_USE_VERTEXAI="false" \
		--set-env-vars GOOGLE_API_KEY=$(GOOGLE_API_KEY) \
		--set-env-vars GENAI_MODEL=$(GENAI_MODEL)

endpoint:
	@gcloud run services describe $(SERVICE_NAME) --region $(REGION) --format 'value(status.url)'

a2a:
	@if [ -n "$(SERVICE_URL)" ]; then \
		echo "Fetching agent card from $(SERVICE_URL)..."; \
		curl -s $(SERVICE_URL)/a2a/$(AGENT_NAME)/.well-known/agent-card.json | jq .; \
	else \
		echo "SERVICE_URL not found, fetching from localhost:$(PORT)..."; \
		curl -s http://localhost:$(PORT)/a2a/$(AGENT_NAME)/.well-known/agent-card.json | jq .; \
	fi

test-invoke:
	@URL=$(if $(SERVICE_URL),$(SERVICE_URL),http://localhost:$(PORT)); \
	echo "Testing endpoint at $$URL/a2a/$(AGENT_NAME) with findings and topic..."; \
	curl -s -X POST $$URL/a2a/$(AGENT_NAME) \
	  -H "Content-Type: application/json" \
	  -d '{"jsonrpc": "2.0", "id": "1", "method": "message/send", "params": {"contextId": "test-session", "message": {"role": "user", "parts": [{"text": "RESEARCH FINDINGS:\n$(RESEARCH_FINDINGS)\n\nUSER QUERY:\n$(TOPIC)"}], "messageId": "m1"}}}' | jq .
