#!/bin/bash
# Automated Documentation Embedding Script
# Embeds Javadoc documentation from common model into ChromaDB

set -e

# Get current version from Maven
VERSION=$(mvn help:evaluate -Dexpression=commonmodel.version -q -DforceStdout 2>/dev/null || echo "")

if [ -z "$VERSION" ]; then
    echo "Error: Could not resolve common model version from Maven"
    exit 1
fi

echo "Common Model Version: $VERSION"

DOC_DIR="./docs/common-model-${VERSION}"

# Generate Javadoc if directory doesn't exist
if [ ! -d "$DOC_DIR" ]; then
    echo "Generating Javadoc for version $VERSION..."
    mvn javadoc:javadoc -Dcommonmodel.version=${VERSION}
    
    # Copy generated docs to versioned directory
    mkdir -p "$DOC_DIR"
    cp -r target/site/apidocs/* "$DOC_DIR/" 2>/dev/null || true
fi

# Embed documentation using Python
echo "Embedding documentation into ChromaDB..."
python3 << EOF
from src.embed import embed_directory
import os

doc_dir = "${DOC_DIR}"
version = "${VERSION}"

if os.path.exists(doc_dir):
    results = embed_directory(
        doc_dir,
        version=version,
        overwrite=False  # Incremental update
    )
    print(f"Embedding complete: {results['success']} succeeded, {results['failed']} failed")
    if results['errors']:
        print("Errors:")
        for error in results['errors']:
            print(f"  - {error['file']}: {error['error']}")
else:
    print(f"Error: Documentation directory not found: {doc_dir}")
    exit(1)
EOF

echo "Documentation embedding completed for version $VERSION"

