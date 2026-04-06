# Makefile for AI Course Creator (Multi-Agent System)

.PHONY: install run lint test deploy clean help

help:
	@echo "Available commands:"
	@echo "  install  - Install dependencies using pip"
	@echo "  run      - Start all agent services and the web app locally"
	@echo "  lint     - Run ruff to check for linting issues"
	@echo "  test     - Run pytest for backend and agent tests"
	@echo "  deploy   - Deploy all services to Google Cloud Run"
	@echo "  clean    - Remove temporary files and caches"

install:
	pip install -e ".[dev,lint]"
	for dir in agents/* app; do (cd $$dir && pip install -e .); done

run:
	./run_local.sh

lint:
	ruff check .

test:
	pytest

deploy:
	./deploy.sh

clean:
	@echo "Cleaning up caches and temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".adk" -exec rm -rf {} +
	find . -type f -name "*.log" -delete
	@echo "Clean completed."
