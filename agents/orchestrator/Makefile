.PHONY: all install run test lint format clean

# Default target
all: run

# Install dependencies
install:
	pip install -e .

# Run the orchestrator agent
run:
	./run.sh

# Run tests
test:
	python3 -m pytest test_orchestrator.py

# Lint the code using ruff
lint:
	ruff check .

# Format the code using black
format:
	black .

# Clean up temporary files
clean:
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .adk/session.db
	rm -rf *.egg-info
