FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy source code
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV HOST 0.0.0.0

# Run ADK API Server
CMD ["python3", "adk_app.py", "--host", "0.0.0.0", "--trace_to_cloud", "--a2a"]
