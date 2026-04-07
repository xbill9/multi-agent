FROM python:3.13-slim

WORKDIR /app

# Set PROJECT_ROOT for pip to resolve local dependencies
ENV PROJECT_ROOT=/app

# Copy shared utilities first
COPY shared /app/shared

# Copy the agent source code (including pyproject.toml and agent source)
COPY agents/orchestrator /app/agents/orchestrator

# Set working directory to the agent's folder
WORKDIR /app/agents/orchestrator

# Install the shared utilities first, then the agent
RUN pip install --no-cache-dir /app/shared
RUN pip install --no-cache-dir .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV HOST 0.0.0.0

# Run using the shared package
CMD ["python3", "-m", "shared.adk_app", "--host", "0.0.0.0", "--port", "8080", "--a2a", "--trace_to_cloud", "."]
