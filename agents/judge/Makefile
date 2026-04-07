# Makefile for Judge Agent

PYTHON = python3
PIP = pip3
PORT = 8002

# Find the project root directory
PROJECT_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || pwd)
export PROJECT_ROOT

.PHONY: help install run lint test clean

help:
	@echo "Available targets:"
	@echo "  install  - Install dependencies"
	@echo "  run      - Run the agent locally on port $(PORT)"
	@echo "  lint     - Run linting (ruff)"
	@echo "  test     - Run tests (pytest)"
	@echo "  clean    - Remove temporary files and cache"

install:
	$(PIP) install -e .

run:
	$(PYTHON) -m shared.adk_app --port $(PORT) --a2a

lint:
	ruff check .

test:
	pytest

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .adk/artifacts
	rm -rf .pytest_cache
	rm -rf .ruff_cache
