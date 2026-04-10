# Makefile for AI Course Creator (Multi-Agent System)

# Use the current python3 from environment
PYTHON_CMD ?= $(shell which python3)

# Set PYTHONPATH to include the project root for shared modules
export PYTHONPATH := $(shell pwd):$(PYTHONPATH)

# Environment variables for local development
export GOOGLE_CLOUD_PROJECT ?= $(shell gcloud config get-value project 2>/dev/null)
export GOOGLE_CLOUD_LOCATION ?= us-central1
export GOOGLE_GENAI_USE_VERTEXAI = False
export LOG_LEVEL = DEBUG
export GENAI_MODEL = gemini-2.5-flash

.PHONY: install run run-local restart-local frontend lint test deploy status check-local endpoint a2a clean help researcher content-builder judge orchestrator course-creator researcher-local judge-local content-builder-local orchestrator-local backend-local frontend-local agents-local stop-local start-local check-frontend build-images deploy-parallel

help:
	@echo "Available commands:"
	@echo "  install               - Install dependencies using pip"
	@echo "  run                   - Start all agent services and the web app locally (alias for start-local)"
	@echo "  run-local             - Alias for run"
	@echo "  restart-local         - Stop and start all local services"
	@echo "  start-local           - Start all agents, backend, and frontend locally in background"
	@echo "  stop-local            - Stop all locally running agents and servers"
	@echo "  agents-local          - Start all four agents (Researcher, Judge, Content Builder, Orchestrator) locally"
	@echo "  researcher-local      - Start the Researcher agent locally on port 8001"
	@echo "  judge-local           - Start the Judge agent locally on port 8002"
	@echo "  content-builder-local - Start the Content Builder agent locally on port 8003"
	@echo "  orchestrator-local    - Start the Orchestrator agent locally on port 8004"
	@echo "  backend-local         - Start the App Backend locally on port 8000"
	@echo "  frontend-local        - Start the Frontend (Vite) dev server"
	@echo "  frontend              - Build the frontend (Vite) to app/dist/"
	@echo "  lint                  - Run ruff to check for linting issues"
	@echo "  test                  - Run pytest for backend and agent tests"
	@echo "  deploy                - Deploy all services to Google Cloud Run (parallel)"
	@echo "  deploy-parallel       - Alias for deploy"
	@echo "  build-images          - Build all service images using Cloud Build"
	@echo "  status                - Check the deployment status on Google Cloud Run"
	@echo "  endpoint              - Show the URLs for all deployed services"
	@echo "  a2a                   - Show the A2A endpoints for all deployed agents"
	@echo "  clean                 - Remove temporary files and caches"

TEST_URL ?= http://localhost:8000
e2e-test:
	@echo "Running end-to-end test against $(TEST_URL)..."
	@curl -s -X POST $(TEST_URL)/api/chat_stream \
		-H "Content-Type: application/json" \
		-d '{"message": "What is the capital of France?", "user_id": "e2e_test_user"}' \
		--no-buffer \
		|| (echo "E2E Test Failed: No valid response from $(TEST_URL)" && exit 1)
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

run: start-local

run-local: start-local

restart-local: start-local

check-frontend:
	@if [ ! -d "app/dist" ]; then \
		echo "Frontend build missing. Building frontend..."; \
		$(MAKE) frontend; \
	fi

researcher-local:
	@echo "Starting Researcher agent locally on port 8001..."
	@/bin/bash -c "source .env 2>/dev/null || true; \
	$(PYTHON_CMD) -m shared.adk_app --host 0.0.0.0 --port 8001 --a2a agents/researcher"

judge-local:
	@echo "Starting Judge agent locally on port 8002..."
	@/bin/bash -c "source .env 2>/dev/null || true; \
	$(PYTHON_CMD) -m shared.adk_app --host 0.0.0.0 --port 8002 --a2a agents/judge"

content-builder-local:
	@echo "Starting Content Builder agent locally on port 8003..."
	@/bin/bash -c "source .env 2>/dev/null || true; \
	$(PYTHON_CMD) -m shared.adk_app --host 0.0.0.0 --port 8003 --a2a agents/content_builder"

orchestrator-local:
	@echo "Starting Orchestrator agent locally on port 8004..."
	@/bin/bash -c "source .env 2>/dev/null || true; \
	export RESEARCHER_AGENT_CARD_URL=http://localhost:8001/a2a/researcher/.well-known/agent-card.json; \
	export JUDGE_AGENT_CARD_URL=http://localhost:8002/a2a/judge/.well-known/agent-card.json; \
	export CONTENT_BUILDER_AGENT_CARD_URL=http://localhost:8003/a2a/content_builder/.well-known/agent-card.json; \
	$(PYTHON_CMD) -m shared.adk_app --host 0.0.0.0 --port 8004 agents/orchestrator"

agents-local: stop-local
	@echo "Starting all agents in background..."
	@nohup $(MAKE) researcher-local > researcher.log 2>&1 &
	@nohup $(MAKE) judge-local > judge.log 2>&1 &
	@nohup $(MAKE) content-builder-local > content_builder.log 2>&1 &
	@echo "Waiting for sub-agents to start..."
	@sleep 5
	@nohup $(MAKE) orchestrator-local > orchestrator.log 2>&1 &
	@echo "All agents started. Logs: researcher.log, judge.log, content_builder.log, orchestrator.log"

start-local: check-frontend agents-local
	@echo "Starting App Backend in background..."
	@nohup $(MAKE) backend-local > backend.log 2>&1 &
	@echo "Starting Frontend dev server in background..."
	@nohup $(MAKE) frontend-local > frontend.log 2>&1 &
	@echo "All services started. Logs: researcher.log, judge.log, content_builder.log, orchestrator.log, backend.log, frontend.log"
	@echo "Frontend: http://localhost:5173"
	@echo "Backend:  http://localhost:8000"

stop-local:
	@echo "Stopping any existing agent and server processes..."
	@pkill -9 -f "[s]hared[.]adk_app" 2>/dev/null || true
	@pkill -9 -f "[m]ain[.]py" 2>/dev/null || true
	@pkill -9 -f "[v]ite" 2>/dev/null || true

backend-local:
	@echo "Starting App Backend locally on port 8000..."
	@/bin/bash -c "source .env 2>/dev/null || true; \
	export AGENT_SERVER_URL=http://localhost:8004; \
	export AGENT_NAME=orchestrator; \
	export PORT=8000; \
	cd app && $(PYTHON_CMD) main.py"

frontend-local:
	@echo "Starting Frontend (Vite) dev server..."
	@/bin/bash -c "cd app/frontend && npm run dev -- --host 0.0.0.0"

frontend:
	make -C app build-frontend

lint:
	ruff check .

test:
	python -m pytest

deploy: deploy-parallel

build-images:
	@if [ -z "${GOOGLE_CLOUD_PROJECT}" ]; then \
		echo "ERROR: GOOGLE_CLOUD_PROJECT is not set. Run 'gcloud config set project' or set the variable."; \
		exit 1; \
	fi
	@echo "Building all images using Cloud Build for project ${GOOGLE_CLOUD_PROJECT}..."
	gcloud builds submit --project "${GOOGLE_CLOUD_PROJECT}" --config cloudbuild.yaml .

deploy-parallel: build-images
	@echo "Deploying sub-agents in parallel..."
	@$(MAKE) -j 3 researcher content-builder judge
	@echo "Deploying orchestrator..."
	@$(MAKE) orchestrator
	@echo "Deploying course-creator app..."
	@$(MAKE) course-creator

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

check-local:
	@echo "Checking status of locally running agents and servers..."
	@echo "--- Network Status ---"
	@netstat -tulnp 2>/dev/null | grep -E "8000|8001|8002|8003|8004|5173" || echo "No services listening on expected ports (8000-8004, 5173)."
	@echo "--- Process Status ---"
	@ps aux | grep -E "[s]hared[.]adk_app|[m]ain[.]py|[v]ite" || echo "No matching processes found."

endpoint:
	@echo "Service URLs:"
	@gcloud run services list --filter="metadata.name:(researcher,content-builder,judge,orchestrator,course-creator)" --format="table(name,status.url)"

a2a:
	@echo "A2A Endpoints (from agents/):"
	@AGENTS=$$(find agents -maxdepth 2 \( -name "agent.json" -o -name "agent.py" \) | xargs -n1 dirname | xargs -n1 basename | sort -u | paste -sd, -); \
	gcloud run services list --filter="metadata.name:($$AGENTS)" --format="value(status.url,metadata.name)" | while read url name; do \
		echo "$$name: $$url/a2a/$$name"; \
	done

clean:
	@echo "Cleaning up caches and temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".adk" -exec rm -rf {} +
	find . -type f -name "*.log" -delete
	@echo "Clean completed."
