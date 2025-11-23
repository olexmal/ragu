#!/bin/bash
# Generate API Key Script
# Generates a secure API key for authentication

python3 << 'EOF'
from src.auth import generate_api_key
import sys

try:
    key = generate_api_key()
    print("Generated API Key:")
    print(key)
    print("\nAdd this to your .env file:")
    print(f"API_KEY={key}")
    print("\nOr set it as an environment variable:")
    print(f"export API_KEY={key}")
except ImportError:
    print("Error: Could not import auth module. Make sure you're in the project directory.")
    sys.exit(1)
EOF

