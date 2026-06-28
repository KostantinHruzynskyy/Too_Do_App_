# ═══════════════════════════════════════════════════
#  SKYY – Makefile
#  Common development and deployment commands
# ═══════════════════════════════════════════════════

.PHONY: help install run test seed clean docker-build docker-up lint format

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies
	pip install -r requirements.txt

run: ## Run the development server
	python run.py

test: ## Run tests with pytest
	python -m pytest tests/ -v --tb=short

test-coverage: ## Run tests with coverage report
	python -m pytest tests/ -v --tb=short --cov=app --cov-report=term-missing

seed: ## Seed database with sample data
	python scripts/seed.py

clean: ## Clean cache and temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.db" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf logs/*.log

docker-build: ## Build Docker image
	docker-compose build

docker-up: ## Start Docker Compose stack
	docker-compose up -d

docker-down: ## Stop Docker Compose stack
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

lint: ## Run linters
	python -m flake8 app/ tests/
	python -m mypy app/ --ignore-missing-imports

format: ## Format code with black
	python -m black app/ tests/

security-check: ## Check for security vulnerabilities
	python -m pip audit