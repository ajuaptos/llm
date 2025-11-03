# Makefile for Local-AI-RAG Application

.PHONY: help install run docker-build docker-up docker-down docker-logs docker-shell clean test

# Default target
help:
	@echo "Local-AI-RAG - Available Commands"
	@echo "=================================="
	@echo ""
	@echo "Local Development:"
	@echo "  make install      - Install dependencies and setup"
	@echo "  make run          - Run application locally"
	@echo "  make test         - Run tests"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-up    - Start Docker containers"
	@echo "  make docker-down  - Stop Docker containers"
	@echo "  make docker-logs  - View Docker logs"
	@echo "  make docker-shell - Open shell in container"
	@echo "  make docker-restart - Restart containers"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean        - Clean temporary files"
	@echo "  make clean-docker - Clean Docker resources"
	@echo "  make format       - Format code with black"
	@echo ""

# Local development
install:
	@echo "Installing dependencies..."
	@chmod +x install.sh
	@./install.sh

run:
	@echo "Starting application..."
	@export PYTHONPATH=$(shell pwd) && python3 backend/main.py

test:
	@echo "Running tests..."
	@. venv/bin/activate && pytest tests/

format:
	@echo "Formatting code..."
	@. venv/bin/activate && black backend/

# Docker commands
docker-build:
	@echo "Building Docker image..."
	@docker build -t local-ai-rag:latest .

docker-up:
	@echo "Starting Docker containers..."
	@docker-compose up -d
	@echo "Application available at http://localhost:8000"

docker-down:
	@echo "Stopping Docker containers..."
	@docker-compose down

docker-logs:
	@docker-compose logs -f

docker-shell:
	@docker exec -it local-ai-rag bash

docker-restart:
	@echo "Restarting Docker containers..."
	@docker-compose restart

docker-rebuild:
	@echo "Rebuilding and restarting..."
	@docker-compose up -d --build

# Quick start with Docker
docker-start: docker-build docker-up
	@echo "Docker setup complete!"
	@echo "Access the application at http://localhost:8000"

# Ollama management
ollama-start:
	@echo "Starting Ollama..."
	@ollama serve &

ollama-pull:
	@echo "Pulling required Ollama models..."
	@ollama pull llama3.2:3b
	@ollama pull llama3.2:1b
	@ollama pull nomic-embed-text

ollama-list:
	@ollama list

# Cleanup
clean:
	@echo "Cleaning temporary files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name "*.log" -delete 2>/dev/null || true
	@rm -rf .pytest_cache
	@rm -rf htmlcov
	@rm -rf .coverage
	@echo "Cleanup complete!"

clean-docker:
	@echo "Cleaning Docker resources..."
	@docker-compose down -v
	@docker system prune -f
	@echo "Docker cleanup complete!"

clean-all: clean clean-docker
	@echo "Removing data directory..."
	@rm -rf data/
	@echo "All cleanup complete!"

# Development helpers
dev-setup: install ollama-pull
	@echo "Development environment setup complete!"

# Status check
status:
	@echo "System Status:"
	@echo "=============="
	@echo -n "Docker: "
	@docker --version 2>/dev/null || echo "Not installed"
	@echo -n "Docker Compose: "
	@docker-compose --version 2>/dev/null || echo "Not installed"
	@echo -n "Python: "
	@python3 --version 2>/dev/null || echo "Not installed"
	@echo -n "Ollama: "
	@ollama --version 2>/dev/null || echo "Not installed"
	@echo ""
	@echo -n "Ollama Service: "
	@curl -s http://localhost:11434/api/tags > /dev/null 2>&1 && echo "Running" || echo "Not running"
	@echo ""

# Quick start (everything)
quick-start: dev-setup docker-start
	@echo "Quick start complete! Application is running."
