# GTA Housing Pipeline -- developer entry points.
#
# Targets whose subject matter is not built yet print an explicit message naming
# the phase that will implement them and exit 0. They are honest no-ops, not fake
# successes -- see docs/decisions/0001-tooling-and-ci.md and docs/build-plan.md §6.

.DEFAULT_GOAL := help

.PHONY: help setup verify-sources ingest transform test eval report all lint format typecheck clean

help: ## Show this list of targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

setup: ## Create the venv and install dev dependencies via uv
	uv sync --extra dev

verify-sources: ## Re-check every data source is live (scripts/verify_sources.py, owned by source-scout)
	@if [ ! -f scripts/verify_sources.py ]; then \
		echo "verify-sources: scripts/verify_sources.py does not exist yet -- it is source-scout's Phase 1 deliverable (see docs/build-plan.md §5.3). Nothing to verify."; \
		exit 1; \
	fi
	uv run python scripts/verify_sources.py

ingest: ## Run the extract-and-land pipeline into the bronze layer
	@echo "ingest: not implemented -- ingestion lands in Phase 2 (see docs/build-plan.md §6)"

transform: ## Build bronze -> silver -> gold in DuckDB
	@echo "transform: not implemented -- bronze/silver/gold modelling lands in Phase 2 (see docs/build-plan.md §6)"

test: ## Run the pytest suite (unit + data tests)
	@uv run pytest; status=$$?; \
	if [ $$status -eq 5 ]; then \
		echo "test: no tests collected yet -- application code and its tests land starting Phase 2 (see docs/build-plan.md §6)"; \
		exit 0; \
	fi; \
	exit $$status

eval: ## Run the golden-question evaluation harness and print a scorecard
	@echo "eval: not implemented -- the eval harness lands in Phase 4 (see docs/build-plan.md §6)"

report: ## Regenerate docs/data-quality-report.md and docs/eval-report.md from committed run output
	@echo "report: not implemented -- data-quality-report.md lands in Phase 2, eval-report.md lands in Phase 4 (see docs/build-plan.md §6)"

all: setup lint typecheck test ## Run setup, lint, typecheck, and test in sequence

lint: ## Run ruff lint checks
	uv run ruff check .

format: ## Apply ruff formatting
	uv run ruff format .

typecheck: ## Run mypy static type checks on src/
	@if find src -name '*.py' 2>/dev/null | grep -q .; then \
		uv run mypy src; \
	else \
		echo "typecheck: no Python files under src/ yet -- nothing to check (application code lands starting Phase 2, see docs/build-plan.md §6)"; \
	fi

clean: ## Remove caches, build artifacts, and the local venv
	rm -rf .venv .pytest_cache .ruff_cache .mypy_cache dist build
	find . -type d -name '__pycache__' -not -path './.venv/*' -exec rm -rf {} +
