#!/bin/sh
set -e

# Start Ollama in background
ollama serve &

# Wait for Ollama to be ready
echo "Waiting for Ollama to start..."
sleep 5

# Pull required models if they don't exist
echo "Checking for required models..."

if ! ollama list | grep -q "mistral"; then
    echo "Pulling mistral model..."
    ollama pull mistral
else
    echo "mistral model already available"
fi

if ! ollama list | grep -q "nomic-embed-text"; then
    echo "Pulling nomic-embed-text model..."
    ollama pull nomic-embed-text
else
    echo "nomic-embed-text model already available"
fi

echo "Ollama setup complete. Models available:"
ollama list

# Keep the container running
wait

