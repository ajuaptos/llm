#!/bin/bash

# Docker Build and Run Script for Local-AI-RAG

set -e

echo "=========================================="
echo "  Local-AI-RAG Docker Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
echo "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed.${NC}"
    echo "Please install Docker from: https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✓ Docker found${NC}"

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose found${NC}"

# Check if Ollama is running on host
echo ""
echo "Checking if Ollama is running on host..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama is running${NC}"
else
    echo -e "${YELLOW}⚠ Warning: Ollama not detected on localhost:11434${NC}"
    echo "Make sure Ollama is running before using the application:"
    echo "  ollama serve"
    echo ""
fi

# Check required models
echo ""
echo "Checking Ollama models..."
if curl -s http://localhost:11434/api/tags 2>/dev/null | grep -q "llama3.2:3b"; then
    echo -e "${GREEN}✓ llama3.2:3b found${NC}"
else
    echo -e "${YELLOW}⚠ llama3.2:3b not found${NC}"
    echo "  Pull with: ollama pull llama3.2:3b"
fi

if curl -s http://localhost:11434/api/tags 2>/dev/null | grep -q "llama3.2:1b"; then
    echo -e "${GREEN}✓ llama3.2:1b found${NC}"
else
    echo -e "${YELLOW}⚠ llama3.2:1b not found${NC}"
    echo "  Pull with: ollama pull llama3.2:1b"
fi

if curl -s http://localhost:11434/api/tags 2>/dev/null | grep -q "nomic-embed-text"; then
    echo -e "${GREEN}✓ nomic-embed-text found${NC}"
else
    echo -e "${YELLOW}⚠ nomic-embed-text not found${NC}"
    echo "  Pull with: ollama pull nomic-embed-text"
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created${NC}"
    echo "Edit .env file to add Google API credentials for Scout feature"
fi

# Create data directory
mkdir -p data

echo ""
echo "=========================================="
echo "  Building Docker Image"
echo "=========================================="
echo ""

# Build the image
docker build -t local-ai-rag:latest .

echo ""
echo -e "${GREEN}✓ Docker image built successfully${NC}"
echo ""
echo "=========================================="
echo "  Starting Application"
echo "=========================================="
echo ""

# Start with docker-compose
docker-compose up -d

echo ""
echo -e "${GREEN}✓ Application started${NC}"
echo ""
echo "=========================================="
echo "  Application Ready!"
echo "=========================================="
echo ""
echo "Access the application at: ${GREEN}http://localhost:8000${NC}"
echo ""
echo "Useful commands:"
echo "  View logs:        docker-compose logs -f"
echo "  Stop:             docker-compose down"
echo "  Restart:          docker-compose restart"
echo "  Rebuild:          docker-compose up -d --build"
echo "  Shell access:     docker exec -it local-ai-rag bash"
echo ""
echo "Make sure Ollama is running on your host machine!"
echo ""
