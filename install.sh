#!/bin/bash

# Local-AI-RAG Installation Script
# This script sets up the complete Local-AI-RAG application

set -e

echo "=========================================="
echo "  Local-AI-RAG Installation Script"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Found Python $PYTHON_VERSION"

# Check if Ollama is installed
echo ""
echo "Checking for Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "Warning: Ollama is not installed or not in PATH."
    echo "Please install Ollama from: https://ollama.ai"
    echo ""
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "Ollama found!"
fi

# Create virtual environment
echo ""
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your configuration (especially Google API keys for Scout feature)"
fi

# Create data directory
echo ""
echo "Creating data directories..."
mkdir -p data
mkdir -p data/chroma

# Pull Ollama models if Ollama is available
if command -v ollama &> /dev/null; then
    echo ""
    echo "Pulling Ollama models..."
    echo "This may take a while depending on your internet connection..."
    
    echo "Pulling llama3.2:3b (main model)..."
    ollama pull llama3.2:3b || echo "Warning: Failed to pull llama3.2:3b"
    
    echo "Pulling llama3.2:1b (scout model)..."
    ollama pull llama3.2:1b || echo "Warning: Failed to pull llama3.2:1b"
    
    echo "Pulling nomic-embed-text (embedding model)..."
    ollama pull nomic-embed-text || echo "Warning: Failed to pull nomic-embed-text"
fi

echo ""
echo "=========================================="
echo "  Installation Complete!"
echo "=========================================="
echo ""
echo "To start the application:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Start the server: python backend/main.py"
echo "  3. Open browser: http://localhost:8000"
echo ""
echo "Optional configuration:"
echo "  - Edit .env file for custom settings"
echo "  - Set GOOGLE_API_KEY and GOOGLE_CSE_ID for Search Scout feature"
echo ""
echo "Make sure Ollama is running before starting the application!"
echo "  Start Ollama: ollama serve"
echo ""
