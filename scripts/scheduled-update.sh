#!/bin/bash
# Scheduled Documentation Update Script
# Designed to be run via cron or systemd timer
# Checks for version changes and updates documentation automatically

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# Log file
LOG_FILE="${PROJECT_DIR}/logs/scheduled-update.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting scheduled documentation update check..."

# Load environment variables if .env exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if update script exists
if [ ! -f "$PROJECT_DIR/scripts/update-docs.sh" ]; then
    log "Error: update-docs.sh not found"
    exit 1
fi

# Run update script
log "Running update-docs.sh..."
if "$PROJECT_DIR/scripts/update-docs.sh" >> "$LOG_FILE" 2>&1; then
    log "Documentation update completed successfully"
    exit 0
else
    log "Error: Documentation update failed"
    exit 1
fi

