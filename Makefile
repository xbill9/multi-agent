# Makefile for AI Course Creator (Multi-Agent System)

.PHONY: install run lint test deploy status endpoint clean help researcher content-builder judge orchestrator course-creator

help:
	@echo "Available commands:"
	@echo "  install          - Install dependencies using pip"
	@echo "  run              - Start all agent services and the web app locally"
	@echo "  lint             - Run ruff to check for linting issues"
	@echo "  test             - Run pytest for backend and agent tests"
	@echo "  deploy           - Deploy all services to Google Cloud Run"
	@echo "  researcher       - Deploy Researcher agent remotely"
	@echo "  content-builder  - Deploy Content Builder agent remotely"
	@echo "  judge            - Deploy Judge agent remotely"
	@echo "  orchestrator     - Deploy Orchestrator agent remotely"
	@echo "  course-creator   - Deploy App Server remotely"
	@echo "  status           - Check the deployment status on Google Cloud Run"
	@echo "  endpoint         - Show the URLs for all deployed services"
	@echo "  clean            - Remove temporary files and caches"

install:
	pip install -e ".[dev,lint]"
	for dir in agents/* app; do (cd $$dir && pip install -e .); done

run:
	./run_local.sh

lint:
	ruff check .

test:
	python -m pytest

deploy:
	./deploy.sh

researcher:
	./deploy.sh researcher

content-builder:
	./deploy.sh content-builder

judge:
	./deploy.sh judge

orchestrator:
	./deploy.sh orchestrator

course-creator:
	./deploy.sh course-creator

status:
	@echo "Checking deployment status for AI Course Creator services..."
	@gcloud run services list --filter="metadata.name:(researcher,content-builder,judge,orchestrator,course-creator)"

endpoint:
	@echo "Service URLs:"
	@gcloud run services list --filter="metadata.name:(researcher,content-builder,judge,orchestrator,course-creator)" --format="table(name,status.url)"

clean:
	@echo "Cleaning up caches and temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".adk" -exec rm -rf {} +
	find . -type f -name "*.log" -delete
	@echo "Clean completed."
