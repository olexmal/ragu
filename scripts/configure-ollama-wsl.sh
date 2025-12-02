#!/bin/bash
# Configure Ollama in WSL to listen on all interfaces (0.0.0.0) so Docker containers can access it
# This script modifies the systemd service to make Ollama accessible from Docker containers

set -e

OLLAMA_SERVICE_FILE="/etc/systemd/system/ollama.service"
BACKUP_FILE="/etc/systemd/system/ollama.service.backup.$(date +%Y%m%d_%H%M%S)"

echo "🔧 Configuring Ollama to listen on all interfaces for Docker access..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ This script must be run with sudo"
    echo "Usage: sudo ./scripts/configure-ollama-wsl.sh"
    exit 1
fi

# Check if Ollama service exists
if [ ! -f "$OLLAMA_SERVICE_FILE" ]; then
    echo "❌ Ollama service file not found at $OLLAMA_SERVICE_FILE"
    echo "   Make sure Ollama is installed and running as a systemd service"
    exit 1
fi

# Check if OLLAMA_HOST is already configured
if grep -q "OLLAMA_HOST" "$OLLAMA_SERVICE_FILE"; then
    echo "⚠️  OLLAMA_HOST is already configured in the service file"
    echo "   Current configuration:"
    grep "OLLAMA_HOST" "$OLLAMA_SERVICE_FILE"
    read -p "Do you want to update it? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
fi

# Create backup
echo "📦 Creating backup of service file..."
cp "$OLLAMA_SERVICE_FILE" "$BACKUP_FILE"
echo "   Backup saved to: $BACKUP_FILE"

# Check if Environment line exists in [Service] section
if grep -q "^Environment=" "$OLLAMA_SERVICE_FILE"; then
    # Update existing Environment line
    echo "✏️  Updating existing Environment variable..."
    sed -i 's|^Environment=.*|Environment="OLLAMA_HOST=0.0.0.0:11434"|' "$OLLAMA_SERVICE_FILE"
else
    # Add Environment line after ExecStart
    echo "➕ Adding OLLAMA_HOST environment variable..."
    sed -i '/^ExecStart=.*ollama serve/a Environment="OLLAMA_HOST=0.0.0.0:11434"' "$OLLAMA_SERVICE_FILE"
fi

# Reload systemd
echo "🔄 Reloading systemd daemon..."
systemctl daemon-reload

# Restart Ollama service
echo "🔄 Restarting Ollama service..."
systemctl restart ollama

# Wait a moment for service to start
sleep 2

# Verify service is running
if systemctl is-active --quiet ollama; then
    echo "✅ Ollama service restarted successfully"
else
    echo "❌ Failed to restart Ollama service"
    echo "   Restoring backup..."
    cp "$BACKUP_FILE" "$OLLAMA_SERVICE_FILE"
    systemctl daemon-reload
    systemctl restart ollama
    exit 1
fi

# Verify Ollama is listening on all interfaces
echo "🔍 Verifying Ollama is listening on all interfaces..."
sleep 2
if netstat -tuln 2>/dev/null | grep -q "0.0.0.0:11434" || ss -tuln 2>/dev/null | grep -q "0.0.0.0:11434"; then
    echo "✅ Ollama is now listening on 0.0.0.0:11434 (all interfaces)"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Get your WSL IP address:"
    echo "      ip addr show eth0 | grep 'inet ' | awk '{print \$2}' | cut -d/ -f1"
    echo ""
    echo "   2. Update your .env file or docker-compose.yml with:"
    echo "      OLLAMA_BASE_URL=http://<WSL_IP>:11434"
    echo ""
    echo "   3. Restart Docker containers:"
    echo "      docker compose restart backend celery-worker"
else
    echo "⚠️  Ollama may still be listening on localhost only"
    echo "   Check with: netstat -tuln | grep 11434"
    echo "   Or: ss -tuln | grep 11434"
fi

echo ""
echo "✨ Configuration complete!"

