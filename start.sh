#!/bin/bash

# Local-AI-RAG Startup Script
# This script starts the FastAPI backend server

echo "🚀 Starting Local-AI-RAG Application..."
echo ""

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Warning: Ollama doesn't seem to be running on localhost:11434"
    echo "   Please start Ollama with: ollama serve"
    echo ""
fi

# Set Python path and start the server
export PYTHONPATH=$(pwd)
echo "📂 Working directory: $(pwd)"
echo "🐍 Python path: $PYTHONPATH"
echo "🌐 Server will be available at: http://localhost:8000"
echo ""

# Start the application
python3 backend/main.py
