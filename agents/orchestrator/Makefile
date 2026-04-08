# Deployment variables
REGION ?= us-central1
GOOGLE_CLOUD_PROJECT ?= $(shell gcloud config get-value project)
GENAI_MODEL ?= gemini-2.5-flash
PORT ?= 8080
SERVICE_URL ?= $(shell gcloud run services describe orchestrator --region $(REGION) --format='value(status.url)' --project $(GOOGLE_CLOUD_PROJECT) 2>/dev/null)

.PHONY: all install run deploy a2a endpoint test lint format clean status

# Default target
all: run

help:
	@echo "Available targets:"
	@echo "  install  - Install dependencies"
	@echo "  run      - Run the orchestrator locally"
	@echo "  status   - Check local and remote service status"
	@echo "  deploy   - Deploy to Cloud Run"
	@echo "  endpoint - Get the deployed service URL"
	@echo "  a2a      - Fetch the A2A Agent Card"
	@echo "  test     - Run tests"
	@echo "  lint     - Run linting"
	@echo "  format   - Run formatting"
	@echo "  clean    - Clean temporary files"

status:
	@echo "--- Local Status (Port $(PORT)) ---"
	@if lsof -Pi :$(PORT) -sTCP:LISTEN -t >/dev/null; then \
		echo "Agent is RUNNING on port $(PORT)"; \
	else \
		echo "Agent is NOT RUNNING locally"; \
	fi
	@echo "--- Cloud Run Status (orchestrator) ---"
	@if [ -n "$(SERVICE_URL)" ]; then \
		echo "Service is DEPLOYED at $(SERVICE_URL)"; \
	else \
		echo "Service is NOT DEPLOYED to Cloud Run"; \
	fi

# Install dependencies
install:
	pip install -e .

# Run the orchestrator agent
run:
	./run.sh

# Deploy to Cloud Run
deploy:
	@echo "Deploying orchestrator..."
	$(eval RESEARCHER_URL=$(shell gcloud run services describe researcher --region $(REGION) --format='value(status.url)' --project $(GOOGLE_CLOUD_PROJECT)))
	$(eval CONTENT_BUILDER_URL=$(shell gcloud run services describe content-builder --region $(REGION) --format='value(status.url)' --project $(GOOGLE_CLOUD_PROJECT)))
	$(eval JUDGE_URL=$(shell gcloud run services describe judge --region $(REGION) --format='value(status.url)' --project $(GOOGLE_CLOUD_PROJECT)))
	gcloud run deploy orchestrator \
		--source . \
		--project $(GOOGLE_CLOUD_PROJECT) \
		--region $(REGION) \
		--allow-unauthenticated \
		--set-env-vars RESEARCHER_AGENT_CARD_URL=$(RESEARCHER_URL)/a2a/agent/.well-known/agent-card.json \
		--set-env-vars JUDGE_AGENT_CARD_URL=$(JUDGE_URL)/a2a/agent/.well-known/agent-card.json \
		--set-env-vars CONTENT_BUILDER_AGENT_CARD_URL=$(CONTENT_BUILDER_URL)/a2a/agent/.well-known/agent-card.json \
		--set-env-vars GOOGLE_CLOUD_PROJECT="$(GOOGLE_CLOUD_PROJECT)" \
		--set-env-vars GOOGLE_GENAI_USE_VERTEXAI="false" \
		--set-env-vars GOOGLE_API_KEY="$(GOOGLE_API_KEY)" \
		--set-env-vars GENAI_MODEL="$(GENAI_MODEL)"

# Get the deployed service URL
endpoint:
	@gcloud run services describe orchestrator --region $(REGION) --format='value(status.url)' --project $(GOOGLE_CLOUD_PROJECT)

# Get the A2A Agent Card
a2a:
	$(eval URL=$(shell gcloud run services describe orchestrator --region $(REGION) --format='value(status.url)' --project $(GOOGLE_CLOUD_PROJECT)))
	@curl -s $(URL)/a2a/agent/.well-known/agent-card.json | jq .

# Run tests
test:
	PYTHONPATH=../.. pytest test_orchestrator.py

# Lint the code using ruff
lint:
	ruff check .

# Format the code using black
format:
	black .

# Clean up temporary files
clean:
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .adk/session.db
	rm -rf *.egg-info
