# Papers API Development Makefile

.PHONY: help install dev test lint format security clean docs run build docker

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation
install: ## Install production dependencies
	poetry install --only=main

dev: ## Install all dependencies (including dev)
	poetry install
	poetry run pre-commit install

# Code Quality
lint: ## Run linting checks
	poetry run ruff check .
	poetry run mypy .
	poetry run bandit -c pyproject.toml -r .

format: ## Format code
	poetry run black .
	poetry run isort .
	poetry run ruff --fix .

security: ## Run security checks
	poetry run bandit -c pyproject.toml -r .
	poetry run safety check

# Testing
test: ## Run tests
	poetry run pytest

test-unit: ## Run unit tests only
	poetry run pytest tests/unit/ -v

test-integration: ## Run integration tests only
	poetry run pytest tests/integration/ -v

test-cov: ## Run tests with coverage
	poetry run pytest --cov=app --cov-report=html --cov-report=term

test-fast: ## Run fast tests (exclude slow tests)
	poetry run pytest -m "not slow"

# Development
run: ## Run development server
	poetry run uvicorn app.server:app --reload --host 0.0.0.0 --port 8000

run-prod: ## Run production server
	poetry run uvicorn app.server:app --host 0.0.0.0 --port 8000

# Database
db-init: ## Initialize database
	poetry run python scripts/init_db.py

db-migrate: ## Run database migrations (if using Alembic)
	@echo "Database migrations not configured yet"

# ETL & Data
crawl: ## Run crawler
	poetry run python crawler/dbpia_crawler.py

etl: ## Run ETL pipeline
	poetry run python scripts/etl.py

add-index: ## Add HNSW index
	poetry run python scripts/add_hnsw_index.py

tune-hnsw: ## Run HNSW parameter tuning
	poetry run python scripts/hnsw_parameter_tuning.py

# Documentation
docs: ## Generate documentation
	@echo "Documentation generation not configured yet"
	# poetry run mkdocs serve

docs-build: ## Build documentation
	@echo "Documentation build not configured yet"
	# poetry run mkdocs build

# Docker
docker-build: ## Build Docker image
	docker build -t papers-api:latest .

docker-run: ## Run Docker container
	docker-compose up

docker-dev: ## Run development environment with Docker
	docker-compose -f docker-compose.dev.yml up

# Cleanup
clean: ## Clean up build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ htmlcov/ .coverage

clean-data: ## Clean up data files (use with caution)
	rm -rf data/pdfs/*
	rm -rf logs/*

# CI/CD
ci: lint security test ## Run all CI checks

pre-commit: ## Run pre-commit hooks on all files
	poetry run pre-commit run --all-files

# Version management
version-patch: ## Bump patch version
	poetry version patch

version-minor: ## Bump minor version
	poetry version minor

version-major: ## Bump major version
	poetry version major

# Environment
env-example: ## Copy environment example
	cp .env.example .env
	@echo "Please edit .env file with your configuration"

# Monitoring
logs: ## Show application logs
	tail -f logs/*.log 2>/dev/null || echo "No log files found"

health-check: ## Check application health
	curl -f http://localhost:8000/health || echo "Application not running"

# Advanced
profile: ## Profile the application
	@echo "Profiling not configured yet"

benchmark: ## Run performance benchmarks
	@echo "Benchmarking not configured yet"

# All-in-one commands
setup: dev env-example db-init ## Complete setup for new developers
	@echo "Setup complete! Edit .env file and run 'make run'"

check: lint security test ## Run all quality checks

deploy-prep: clean ci version-patch ## Prepare for deployment
	@echo "Ready for deployment"