#!/bin/bash
# Webhook Handler Script
# Handles webhook notifications for version updates
# Can be called from CI/CD pipelines or external systems

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# Log file
LOG_FILE="${PROJECT_DIR}/logs/webhook.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Webhook triggered"

# Parse webhook payload (if provided)
VERSION="${1:-}"
if [ -z "$VERSION" ]; then
    # Try to get version from environment or stdin
    if [ -t 0 ]; then
        # No stdin, try to get from Maven
        VERSION=$(mvn help:evaluate -Dexpression=commonmodel.version -q -DforceStdout 2>/dev/null || echo "")
    else
        # Read from stdin (JSON payload)
        PAYLOAD=$(cat)
        VERSION=$(echo "$PAYLOAD" | python3 -c "import sys, json; print(json.load(sys.stdin).get('version', ''))" 2>/dev/null || echo "")
    fi
fi

if [ -z "$VERSION" ]; then
    log "Error: Version not provided"
    exit 1
fi

log "Processing webhook for version: $VERSION"

# Run update script
if [ -f "$PROJECT_DIR/scripts/update-docs.sh" ]; then
    log "Running update-docs.sh..."
    "$PROJECT_DIR/scripts/update-docs.sh" >> "$LOG_FILE" 2>&1
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        log "Webhook processed successfully"
        exit 0
    else
        log "Error: Update script failed with exit code $EXIT_CODE"
        exit $EXIT_CODE
    fi
else
    log "Error: update-docs.sh not found"
    exit 1
fi

