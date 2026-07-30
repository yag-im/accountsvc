.DEFAULT_GOAL := help
UV ?= uv

.PHONY: help bootstrap format lint typecheck test build docker-build run audit clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

bootstrap: ## Create the virtualenv, install dependencies and git hooks
	$(UV) lock
	$(UV) sync
	$(UV) run pre-commit install --install-hooks

format: ## Auto-format and auto-fix the codebase
	$(UV) run ruff format .
	$(UV) run ruff check --fix .

lint: ## Run linters, formatting checks and static type checking
	$(UV) run ruff check .
	$(UV) run ruff format --check .
	$(MAKE) typecheck

typecheck: ## Run static type checking
	$(UV) run pyright

test: ## Run the test suite
	$(UV) run pytest

build: ## Build the wheel and sdist
	$(UV) build

docker-build: ## Build the container image
	docker build \
		--build-arg APP_VERSION=$$($(UV) run python -c "from accountsvc import __version__; print(__version__)") \
		--build-arg GIT_SHA=$$(git rev-parse --short HEAD 2>/dev/null || echo unknown) \
		--build-arg BUILD_TIMESTAMP=$$(date -u +%Y-%m-%dT%H:%M:%SZ) \
		--tag accountsvc:local .

run: ## Run the service locally
	$(UV) run accountsvc

audit: ## Audit locked dependencies for known vulnerabilities
	$(UV) export --frozen --no-dev --no-emit-project --format requirements-txt | \
		$(UV) run pip-audit --no-deps --requirement /dev/stdin

clean: ## Remove build artefacts and caches
	rm -rf dist build .pytest_cache .ruff_cache .coverage htmlcov
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
