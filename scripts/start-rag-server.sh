#!/bin/bash
# Start RAG Server Script
# Checks prerequisites and starts the Flask API server

set -e

echo "Starting RAG Server..."

# Check if Ollama is running
if ! command -v ollama &> /dev/null; then
    echo "Error: Ollama is not installed or not in PATH"
    echo "Install from: https://ollama.ai/"
    exit 1
fi

# Check if Ollama service is accessible
if ! ollama list &> /dev/null; then
    echo "Warning: Ollama service may not be running"
    echo "Starting Ollama service..."
    ollama serve &
    sleep 2
fi

# Check if required models are available
LLM_MODEL=${LLM_MODEL:-mistral}
EMBED_MODEL=${TEXT_EMBEDDING_MODEL:-nomic-embed-text}

echo "Checking for required models..."
if ! ollama list | grep -q "$LLM_MODEL"; then
    echo "Model $LLM_MODEL not found. Pulling..."
    ollama pull "$LLM_MODEL"
fi

if ! ollama list | grep -q "$EMBED_MODEL"; then
    echo "Model $EMBED_MODEL not found. Pulling..."
    ollama pull "$EMBED_MODEL"
fi

# Check Python environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Using defaults."
    echo "Copy .env.example to .env and configure as needed."
fi

# Start server
echo "Starting RAGU API server..."
cd "$(dirname "$0")/.."

# Check if Gunicorn is available (production mode)
if command -v gunicorn &> /dev/null || python3 -c "import gunicorn" 2>/dev/null; then
    echo "Starting with Gunicorn (production mode)..."
    API_HOST=${API_HOST:-0.0.0.0}
    API_PORT=${API_PORT:-8080}
    gunicorn -c gunicorn_config.py "src.app:app"
else
    echo "Gunicorn not found. Starting with Flask development server..."
    echo "For production, install Gunicorn: pip install gunicorn"
    python3 -c "from src.app import app; import os; app.run(host=os.getenv('API_HOST', 'localhost'), port=int(os.getenv('API_PORT', 8080)), debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true')"
fi

