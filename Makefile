# Makefile for AI Course Creator (Multi-Agent System)

.PHONY: install run frontend lint test deploy status endpoint clean help researcher content-builder judge orchestrator course-creator

help:
	@echo "Available commands:"
	@echo "  install          - Install dependencies using pip"
	@echo "  run              - Start all agent services and the web app locally"
	@echo "  frontend         - Build the frontend (Vite) to app/dist/"
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
	@echo "  e2e-test         - Run a full end-to-end test against the backend (Default: localhost:8000)"
	@echo "  e2e-test-cloud   - Run a full end-to-end test against the Cloud Run deployment"
	@echo "  clean            - Remove temporary files and caches"

TEST_URL ?= http://localhost:8000
e2e-test:
	@echo "Running end-to-end test against $(TEST_URL)..."
	@curl -X POST $(TEST_URL)/api/chat_stream \
		-H "Content-Type: application/json" \
		-d '{"message": "What is the capital of France?", "user_id": "e2e_test_user"}' \		--no-buffer \
		| grep -E "type|text" || (echo "E2E Test Failed: No valid response from $(TEST_URL)" && exit 1)
	@echo "\nE2E Test Completed successfully!"

e2e-test-cloud:
	@CC_URL=$$(gcloud run services describe course-creator --format='value(status.url)' --region $(GOOGLE_CLOUD_LOCATION) 2>/dev/null); \
	if [ -z "$$CC_URL" ]; then \
		echo "ERROR: Could not find course-creator service URL in region $(GOOGLE_CLOUD_LOCATION). Is it deployed?"; \
		exit 1; \
	fi; \
	$(MAKE) e2e-test TEST_URL=$$CC_URL

install:
	pip install -e ".[dev,lint]"
	for dir in agents/* app; do (cd $$dir && pip install -e .); done

run:
	./run_local.sh

frontend:
	make -C app build-frontend

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
