#!/bin/bash
# Docker Logs Script for RAGU
# View logs from Docker Compose services

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

# Parse arguments
SERVICE="${1:-}"
FOLLOW="${2:-}"

if [ -n "$SERVICE" ]; then
    echo "Showing logs for service: $SERVICE"
    if [ "$FOLLOW" = "-f" ] || [ "$FOLLOW" = "--follow" ]; then
        $DOCKER_COMPOSE -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.prod.yml logs -f "$SERVICE"
    else
        $DOCKER_COMPOSE -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.prod.yml logs "$SERVICE"
    fi
else
    echo "Showing logs for all services"
    if [ "$FOLLOW" = "-f" ] || [ "$FOLLOW" = "--follow" ]; then
        $DOCKER_COMPOSE -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.prod.yml logs -f
    else
        $DOCKER_COMPOSE -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.prod.yml logs
    fi
fi

