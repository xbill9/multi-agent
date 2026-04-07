# Makefile for AI Course Creator Web App

.PHONY: install build-frontend run lint test clean help

help:
	@echo "Available commands:"
	@echo "  install          - Install Python and Frontend dependencies"
	@echo "  build-frontend   - Build the frontend (Vite) to dist/"
	@echo "  run              - Start the FastAPI web app locally"
	@echo "  lint             - Run ruff to check for linting issues"
	@echo "  test             - Run all project tests from the root directory"
	@echo "  clean            - Remove temporary files, caches, and build artifacts"

install:
	pip install -r requirements.txt
	cd frontend && npm install

build-frontend:
	cd frontend && npm run build

run:
	python main.py

lint:
	ruff check .

test:
	make -C .. test

clean:
	@echo "Cleaning up caches and temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf frontend/dist
	rm -rf frontend/node_modules
	@echo "Clean completed."
