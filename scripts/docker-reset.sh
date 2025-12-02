#!/bin/bash
# Docker Reset Script for RAGU
# Stops services and removes volumes (WARNING: This deletes all data!)

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

echo "WARNING: This will stop all services and DELETE all data volumes!"
echo "This includes:"
echo "  - ChromaDB data (all collections)"
echo "  - Redis data"
echo "  - Application logs"
echo "  - Settings"
echo "  - Ollama models (if containerized)"
echo ""
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Reset cancelled."
    exit 0
fi

echo "Stopping services..."
$DOCKER_COMPOSE -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.prod.yml --profile dev --profile prod --profile with-ollama down -v

echo "Removing volumes..."
$DOCKER_COMPOSE -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.prod.yml --profile dev --profile prod --profile with-ollama down --volumes --remove-orphans

echo "Removing images (optional)..."
read -p "Remove Docker images as well? (yes/no): " REMOVE_IMAGES

if [ "$REMOVE_IMAGES" = "yes" ]; then
    echo "Removing images..."
    docker rmi ragu-backend ragu-frontend-dev ragu-frontend-prod 2>/dev/null || true
fi

echo "Reset complete. All data has been deleted."

