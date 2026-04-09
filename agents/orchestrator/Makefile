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

# Deploy to Cloud Run using Cloud Build
deploy:
	@echo "Deploying orchestrator using Cloud Build..."
	gcloud builds submit ../.. \
		--project $(GOOGLE_CLOUD_PROJECT) \
		--config cloudbuild.yaml \
		--substitutions=_REGION=$(REGION),_GENAI_MODEL=$(GENAI_MODEL),_GOOGLE_API_KEY=$(GOOGLE_API_KEY)

# Get the deployed service URL
endpoint:
	@gcloud run services describe orchestrator --region $(REGION) --format='value(status.url)' --project $(GOOGLE_CLOUD_PROJECT)

# Get the A2A Agent Card
a2a:
	$(eval URL=$(shell gcloud run services describe orchestrator --region $(REGION) --format='value(status.url)' --project $(GOOGLE_CLOUD_PROJECT)))
	@curl -s $(URL)/a2a/orchestrator/.well-known/agent-card.json | jq .

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
