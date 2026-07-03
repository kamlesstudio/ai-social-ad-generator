.PHONY: help install dev-install test lint format run docker-build docker-up docker-down clean deploy

help:
	@echo "Available commands:"
	@echo "  make install       - Install production dependencies"
	@echo "  make dev-install   - Install development dependencies"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linters"
	@echo "  make format        - Format code"
	@echo "  make run           - Run development server"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-up     - Start Docker containers"
	@echo "  make docker-down   - Stop Docker containers"
	@echo "  make clean         - Clean cache files"
	@echo "  make deploy        - Deploy to GCP"

install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements-dev.txt

test:
	pytest tests/ -v --cov=app --cov-report=html

lint:
	flake8 app/ tests/
	mypy app/
	black --check app/ tests/
	isort --check-only app/ tests/

format:
	black app/ tests/
	isort app/ tests/

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/

deploy:
	./scripts/deploy.sh