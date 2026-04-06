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

# Run
CMD ["python3", "main.py"]
