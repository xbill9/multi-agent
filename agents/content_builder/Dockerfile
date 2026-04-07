FROM python:3.13-slim

WORKDIR /app

# Set PROJECT_ROOT for pip to resolve local dependencies
ENV PROJECT_ROOT=/app

# Copy shared utilities first
COPY shared /app/shared

# Copy the agent source code
COPY agents/content_builder /app/agents/content_builder

# Set working directory to the agent's folder
WORKDIR /app/agents/content_builder

# Install the agent and its dependencies (including the local 'shared-utils')
# Using -e or direct path to shared since PROJECT_ROOT won't exist in Docker
RUN pip install --no-cache-dir /app/shared
RUN pip install --no-cache-dir .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV HOST 0.0.0.0

# Run ADK API Server (now imported from the shared package)
CMD ["python3", "-m", "shared.adk_app", "--host", "0.0.0.0", "--trace_to_cloud", "--a2a"]
