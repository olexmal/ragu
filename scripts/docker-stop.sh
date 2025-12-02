#!/bin/bash
# Docker Stop Script for RAGU
# Stops all Docker Compose services

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# Determine Docker Compose command
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

echo "Stopping RAGU Docker services..."

# Stop all services
$DOCKER_COMPOSE -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.prod.yml --profile dev --profile prod --profile with-ollama down

echo "All services stopped."

