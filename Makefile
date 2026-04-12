# Makefile for AI Course Creator (Multi-Agent System)

# Use the current python3 from environment
PYTHON_CMD ?= $(shell which python3)

# Set PYTHONPATH to include the project root for shared modules
export PYTHONPATH := $(shell pwd):$(PYTHONPATH)

# Environment variables for local development
export LOG_LEVEL = DEBUG
export GENAI_MODEL = gemini-2.5-flash

.PHONY: install start run run-local restart-local local frontend lint test test-researcher test-judge test-content-builder test-orchestrator local researcher content-builder judge orchestrator course-creator researcher-local judge-local content-builder-local orchestrator-local backend-local frontend-local agents-local stop-local start-local check-frontend build-images deploy-aks destroy-aks status-aks endpoint-aks az-destroy clean help

help:
	@echo "Available commands:"
	@echo "  install               - Install all dependencies for root, agents, and app"
	@echo "  start                 - Start all services locally (alias for start-local)"
	@echo "  stop                  - Stop all local services (alias for stop-local)"
	@echo "  run                   - Start all services locally (alias for start-local)"
	@echo "  local                 - Show local service URLs"
	@echo "  start-local           - Start all local services in background"
	@echo "  stop-local            - Stop all local processes"
	@echo "  test                  - Run all tests (pytest)"
	@echo "  test-researcher       - Test the Researcher agent directly"
	@echo "  test-judge            - Test the Judge agent directly"
	@echo "  test-orchestrator     - Test the Orchestrator logic"
	@echo "  e2e-test-aks          - Run end-to-end test against the AKS endpoint"
	@echo "  lint                  - Run linting checks (ruff)"
	@echo "  deploy-aks            - Deploy all services to Azure AKS"
	@echo "  destroy-aks           - Delete AKS resources"
	@echo "  status-aks            - Show AKS status"
	@echo "  endpoint-aks          - Show AKS service endpoint"
	@echo "  az-destroy            - Delete the entire Azure Resource Group"
	@echo "  clean                 - Remove caches and logs"

TEST_URL ?= http://localhost:8000
TEST_MESSAGE ?= "Create a short course about the history of the internet"
e2e-test:
	@echo "Running end-to-end test against $(TEST_URL)..."
	@curl -s --fail -X POST $(TEST_URL)/api/chat_stream \
		-H "Content-Type: application/json" \
		-d '{"message": $(TEST_MESSAGE), "user_id": "e2e_test_user"}' \
		--no-buffer \
		|| (echo "E2E Test Failed: No valid response from $(TEST_URL)" && exit 1)
	@echo "\nE2E Test Completed successfully!"

e2e-test-aks:
	@echo "Fetching AKS LoadBalancer IP..."
	@IP=$$(kubectl get svc course-creator -o jsonpath='{.status.loadBalancer.ingress[0].ip}'); \
	if [ -z "$$IP" ]; then \
		echo "Error: AKS LoadBalancer IP not found or still pending."; \
		exit 1; \
	fi; \
	$(MAKE) e2e-test TEST_URL=http://$$IP

install:
	@echo "Installing root dependencies..."
	pip install -e ".[dev,lint]"
	@echo "Installing agent and app dependencies..."
	for dir in agents/* app; do (cd $$dir && pip install -e .); done
	@echo "Installing frontend dependencies..."
	cd app/frontend && npm install

run: start-local

start: start-local

run-local: start-local

restart-local: start-local

stop: stop-local

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

test-researcher:
	./research_test.sh

test-judge:
	./judge_test.sh

test-orchestrator:
	python agents/orchestrator/test_orchestrator.py

test-content-builder:
	python agents/content_builder/tests/test_agent.py

deploy: deploy-aks

deploy-aks:
	./aks/deploy-aks.sh

destroy-aks:
	@echo "Destroying AKS resources..."
	kubectl delete -f aks/manifests.yaml || true
	kubectl delete secret adk-secrets || true
	@echo "Note: This does not delete the AKS cluster. Use az-destroy if you want to delete the whole group."

az-destroy:
	@AZ_RESOURCE_GROUP=$${AZ_RESOURCE_GROUP:-"adk-rg-aks"}; \
	echo "Destroying Azure Resource Group $$AZ_RESOURCE_GROUP..."; \
	az group delete --name "$$AZ_RESOURCE_GROUP" --yes --no-wait; \
	echo "Resource Group deletion initiated."

status: status-aks

status-aks:
	@echo "Checking AKS Deployment status..."
	@kubectl get deployments
	@kubectl get pods
	@kubectl get services

aks-status: status-aks

local:
	@echo "--- Local Service URLs ---"
	@echo "Frontend: http://localhost:5173"
	@echo "Backend:  http://localhost:8000 (main app)"
	@echo "Agents:"
	@echo "  Researcher:      http://localhost:8001"
	@echo "  Judge:           http://localhost:8002"
	@echo "  Content Builder: http://localhost:8003"
	@echo "  Orchestrator:    http://localhost:8004"

check-local:
	@echo "Checking status of locally running agents and servers..."
	@echo "--- Network Status ---"
	@netstat -tulnp 2>/dev/null | grep -E "8000|8001|8002|8003|8004|5173" || echo "No services listening on expected ports (8000-8004, 5173)."
	@echo "--- Process Status ---"
	@ps aux | grep -E "[s]hared[.]adk_app|[m]ain[.]py|[v]ite" || echo "No matching processes found."

endpoint: endpoint-aks

endpoint-aks:
	@echo "--- Azure AKS Endpoint ---"
	@kubectl get svc course-creator -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "Pending..."
	@echo ""

clean:
	@echo "Cleaning up caches and temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".adk" -exec rm -rf {} +
	find . -type f -name "*.log" -delete
	@echo "Clean completed."
