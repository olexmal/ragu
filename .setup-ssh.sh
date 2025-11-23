#!/bin/bash
# SSH Agent setup script for git operations

# Start SSH agent if not running
if [ -z "$SSH_AUTH_SOCK" ]; then
    eval "$(ssh-agent -s)"
    echo "SSH agent started"
fi

# Add SSH keys
echo "Adding SSH keys to agent..."
ssh-add ~/.ssh/id_ed25519 2>/dev/null || ssh-add ~/.ssh/id_rsa 2>/dev/null

# Test GitHub connection
echo "Testing GitHub connection..."
ssh -T git@github.com 2>&1 | grep -q "successfully authenticated" && echo "✓ GitHub SSH connection successful!" || echo "⚠ Connection test completed"
