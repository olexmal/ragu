#!/bin/bash
# Update Documentation Script
# Checks for version changes and automatically updates embedded documentation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# Load environment variables if .env exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Get current version from Maven
CURRENT_VERSION=$(mvn help:evaluate -Dexpression=${COMMON_MODEL_VERSION_PROPERTY:-commonmodel.version} -q -DforceStdout 2>/dev/null || echo "")

if [ -z "$CURRENT_VERSION" ]; then
    echo "Error: Could not resolve common model version from Maven"
    exit 1
fi

echo "Current Common Model Version: $CURRENT_VERSION"

# Check if version tracking file exists
VERSION_FILE=".rag-versions.json"
LAST_VERSION=""

if [ -f "$VERSION_FILE" ]; then
    LAST_VERSION=$(python3 << EOF
import json
try:
    with open("$VERSION_FILE", "r") as f:
        data = json.load(f)
        print(data.get("last_embedded_version", ""))
except:
    print("")
EOF
)
fi

# Check if version has changed
if [ "$CURRENT_VERSION" = "$LAST_VERSION" ]; then
    echo "Version unchanged ($CURRENT_VERSION). Documentation is up to date."
    exit 0
fi

echo "Version changed from '$LAST_VERSION' to '$CURRENT_VERSION'"
echo "Updating documentation..."

# Run embedding script
./scripts/embed-commonmodel-docs.sh

# Update version tracking file
python3 << EOF
import json
import os

version_file = "$VERSION_FILE"
current_version = "$CURRENT_VERSION"

data = {}
if os.path.exists(version_file):
    with open(version_file, "r") as f:
        data = json.load(f)

data["last_embedded_version"] = current_version
data["last_update"] = __import__("datetime").datetime.now().isoformat()

with open(version_file, "w") as f:
    json.dump(data, f, indent=2)

print(f"Updated version tracking: {current_version}")
EOF

echo "Documentation update completed for version $CURRENT_VERSION"

