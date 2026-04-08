# Top-level Makefile for traversing agent subdirectories

SUBDIRS = researcher judge content_builder orchestrator

.PHONY: help install lint test clean deploy format run endpoint a2a status

help:
	@echo "Available targets:"
	@echo "  install  - Install dependencies for all agents"
	@echo "  lint     - Run linting for all agents"
	@echo "  test     - Run tests for all agents"
	@echo "  status   - Check the status of all agents (local and remote)"
	@echo "  clean    - Clean temporary files for all agents"
	@echo "  deploy   - Deploy all agents to Cloud Run (if supported)"
	@echo "  format   - Run formatting for all agents (if supported)"
	@echo "  run      - Run all agents in parallel"
	@echo "  endpoint - Get the deployed service URLs for all agents"
	@echo "  a2a      - Fetch the A2A Agent Cards for all agents"

install lint test clean status:
	@for dir in $(SUBDIRS); do \
		echo "--- $$dir: $@ ---"; \
		$(MAKE) -C $$dir $@; \
	done

deploy format endpoint a2a:
	@for dir in $(SUBDIRS); do \
		if grep -q "^$@:" $$dir/Makefile; then \
			echo "--- $$dir: $@ ---"; \
			$(MAKE) -C $$dir $@; \
		else \
			echo "--- $$dir: Skipping $@ (not supported) ---"; \
		fi \
	done

run:
	@echo "--- Starting all agents in parallel ---"
	@for dir in $(SUBDIRS); do \
		(cd $$dir && $(MAKE) run) & \
	done; \
	wait
