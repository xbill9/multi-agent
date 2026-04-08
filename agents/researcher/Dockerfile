FROM python:3.13-slim

WORKDIR /app

# Copy all source (root context)
COPY . .

# Install shared and agent
RUN pip install --no-cache-dir ./shared
RUN pip install --no-cache-dir ./agents/researcher

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV HOST 0.0.0.0

# Run ADK API Server
# Looking for agents/researcher/agent.py (AgentLoader expects the directory)
CMD ["python3", "-m", "shared.adk_app", "/app/agents", "--host", "0.0.0.0", "--trace_to_cloud", "--a2a"]
