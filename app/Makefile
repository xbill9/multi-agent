# Makefile for AI Course Creator Web App

# Cloud Run Deployment Variables
PROJECT_ID   ?= $(shell gcloud config get-value project)
REGION       ?= us-central1
SERVICE_NAME ?= course-creator
ORCHESTRATOR_URL = $(shell gcloud run services describe orchestrator --region $(REGION) --format='value(status.url)' --project $(PROJECT_ID) 2>/dev/null)

.PHONY: install build-frontend run lint test clean help deploy

help:
	@echo "Available commands:"
	@echo "  install          - Install Python and Frontend dependencies"
	@echo "  build-frontend   - Build the frontend (Vite) to dist/"
	@echo "  run              - Start the FastAPI web app locally"
	@echo "  lint             - Run ruff to check for linting issues"
	@echo "  test             - Run all project tests from the root directory"
	@echo "  clean            - Remove temporary files, caches, and build artifacts"
	@echo "  deploy           - Deploy the web app to Cloud Run"

install:
	pip install -r requirements.txt
	cd frontend && npm install

build-frontend:
	cd frontend && npm run build

run:
	python main.py

lint:
	ruff check .

test:
	make -C .. test

deploy:
	@echo "Deploying to Cloud Run ($(SERVICE_NAME)) in project $(PROJECT_ID)..."
	gcloud run deploy $(SERVICE_NAME) \
		--source . \
		--project $(PROJECT_ID) \
		--region $(REGION) \
		--allow-unauthenticated \
		--set-env-vars AGENT_SERVER_URL=$(ORCHESTRATOR_URL)

clean:
	@echo "Cleaning up caches and temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf frontend/dist
	rm -rf frontend/node_modules
	@echo "Clean completed."
