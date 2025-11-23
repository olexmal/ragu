#!/bin/bash
# Setup Cron Job for Scheduled Documentation Updates
# This script helps set up a cron job to automatically check for documentation updates

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

CRON_SCHEDULE="${1:-0 */6 * * *}"  # Default: every 6 hours
SCRIPT_PATH="$PROJECT_DIR/scripts/scheduled-update.sh"

echo "Setting up cron job for RAG documentation updates"
echo "Schedule: $CRON_SCHEDULE"
echo "Script: $SCRIPT_PATH"
echo ""

# Create logs directory
mkdir -p "$PROJECT_DIR/logs"

# Check if cron job already exists
CRON_CMD="$CRON_SCHEDULE $SCRIPT_PATH >> $PROJECT_DIR/logs/cron.log 2>&1"

if crontab -l 2>/dev/null | grep -q "$SCRIPT_PATH"; then
    echo "Cron job already exists. Removing old entry..."
    crontab -l 2>/dev/null | grep -v "$SCRIPT_PATH" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

echo "Cron job installed successfully!"
echo ""
echo "To view current cron jobs: crontab -l"
echo "To remove this cron job: crontab -e (then delete the line)"
echo ""
echo "Logs will be written to: $PROJECT_DIR/logs/"

