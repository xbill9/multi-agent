# --- Stage 1: Build Frontend ---
FROM node:25-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build && ls -R /app/dist

# --- Stage 2: Final Image ---
FROM python:3.13-slim
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY . .

# Copy built frontend from Stage 1
COPY --from=frontend-builder /app/dist ./dist
RUN ls -R /app/dist

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV HOST 0.0.0.0

# Port for Cloud Run (default is 8080)
EXPOSE 8080

# Run
CMD ["python3", "main.py"]
