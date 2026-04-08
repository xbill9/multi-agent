#!/bin/bash

# Kill any existing processes (manual cleanup first)
echo "Stopping any existing agent and server processes..."
pkill -9 -f "shared.adk_app" 2>/dev/null || true
pkill -9 -f "main.py" 2>/dev/null || true
pkill -9 -f "vite" 2>/dev/null || true

# Use the Google Cloud SDK bundled Python 3.13
PYTHON_CMD=/usr/lib/google-cloud-sdk/platform/bundledpythonunix/bin/python3
if [ ! -f "$PYTHON_CMD" ]; then
  PYTHON_CMD=python3
fi

# Set common environment variables for local development
if [ -f ".env" ]; then
  source .env
fi
export GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT}"
export GOOGLE_CLOUD_LOCATION="${GOOGLE_CLOUD_LOCATION:-us-central1}"
export GOOGLE_GENAI_USE_VERTEXAI="False"
export LOG_LEVEL=DEBUG
export GENAI_MODEL=gemini-2.5-flash

# Ensure frontend is built once
if [ ! -d "app/dist" ]; then
  echo "Building frontend..."
  pushd app/frontend > /dev/null
  npm install --no-progress --silent
  npm run build -- --silent
  popd > /dev/null
fi

echo "Starting agents and servers with DEBUG logging..."

nohup $PYTHON_CMD -m shared.adk_app --host 0.0.0.0 --port 8001 --a2a agents/researcher > researcher.log 2>&1 &
nohup $PYTHON_CMD -m shared.adk_app --host 0.0.0.0 --port 8002 --a2a agents/judge > judge.log 2>&1 &
nohup $PYTHON_CMD -m shared.adk_app --host 0.0.0.0 --port 8003 --a2a agents/content_builder > content_builder.log 2>&1 &

export RESEARCHER_AGENT_CARD_URL=http://localhost:8001/a2a/researcher/.well-known/agent-card.json
export JUDGE_AGENT_CARD_URL=http://localhost:8002/a2a/judge/.well-known/agent-card.json
export CONTENT_BUILDER_AGENT_CARD_URL=http://localhost:8003/a2a/content_builder/.well-known/agent-card.json


nohup $PYTHON_CMD -m shared.adk_app --host 0.0.0.0 --port 8004 agents/orchestrator > orchestrator.log 2>&1 &

# Wait for agents to start
sleep 5

echo "Starting App Backend (8000)..."
export AGENT_SERVER_URL=http://localhost:8004
export AGENT_NAME=orchestrator
export PORT=8000
pushd app > /dev/null
nohup $PYTHON_CMD main.py > ../backend.log 2>&1 &
popd > /dev/null

pushd app/frontend > /dev/null
nohup npm run dev -- --host 0.0.0.0 > ../../frontend.log 2>&1 &
popd > /dev/null

echo "All services started in background with standardized JSON DEBUG logging."
echo "Frontend: http://localhost:5173"
echo "Backend:  http://localhost:8000"
echo "Logs: researcher.log, judge.log, content_builder.log, orchestrator.log, backend.log, frontend.log"
