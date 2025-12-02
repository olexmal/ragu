#!/bin/bash
# Docker Start Script for RAGU
# Starts all services using Docker Compose

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    echo "Install from: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Error: Docker Compose is not installed"
    echo "Install from: https://docs.docker.com/compose/install/"
    exit 1
fi

# Determine Docker Compose command
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

# Parse command line arguments
MODE="${1:-dev}"
OLLAMA_MODE="${2:-external}"

echo "Starting RAGU with Docker Compose..."
echo "Mode: $MODE"
echo "Ollama: $OLLAMA_MODE"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Creating from .env.docker..."
    if [ -f ".env.docker" ]; then
        cp .env.docker .env
    else
        echo "Warning: .env.docker not found. Using defaults."
    fi
fi

# Start services based on mode
if [ "$MODE" = "prod" ]; then
    echo "Starting in PRODUCTION mode..."
    PROFILES="--profile prod"
    
    if [ "$OLLAMA_MODE" = "container" ]; then
        PROFILES="$PROFILES --profile with-ollama"
        echo "Using containerized Ollama"
        export OLLAMA_BASE_URL=http://ollama:11434
    else
        echo "Using external Ollama (ensure it's running on host)"
        if [ -z "$OLLAMA_BASE_URL" ]; then
            export OLLAMA_BASE_URL=http://host.docker.internal:11434
            echo "Set OLLAMA_BASE_URL to http://host.docker.internal:11434"
        fi
    fi
    
    $DOCKER_COMPOSE -f docker-compose.yml -f docker-compose.prod.yml $PROFILES up -d
    
    echo ""
    echo "Services started in production mode (detached)"
    echo "Frontend: http://localhost:80"
    echo "Backend API: http://localhost:8080"
    echo "View logs: ./scripts/docker-logs.sh"
    
elif [ "$MODE" = "dev" ]; then
    echo "Starting in DEVELOPMENT mode..."
    PROFILES="--profile dev"
    
    if [ "$OLLAMA_MODE" = "container" ]; then
        PROFILES="$PROFILES --profile with-ollama"
        echo "Using containerized Ollama"
        export OLLAMA_BASE_URL=http://ollama:11434
    else
        echo "Using external Ollama (ensure it's running on host)"
        if [ -z "$OLLAMA_BASE_URL" ]; then
            export OLLAMA_BASE_URL=http://host.docker.internal:11434
            echo "Set OLLAMA_BASE_URL to http://host.docker.internal:11434"
        fi
    fi
    
    $DOCKER_COMPOSE -f docker-compose.yml -f docker-compose.dev.yml $PROFILES up
    
else
    echo "Error: Invalid mode '$MODE'"
    echo "Usage: $0 [dev|prod] [external|container]"
    echo "  dev       - Development mode with hot reload"
    echo "  prod      - Production mode (detached)"
    echo "  external  - Use external Ollama (default)"
    echo "  container - Use containerized Ollama"
    exit 1
fi

