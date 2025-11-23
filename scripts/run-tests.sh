#!/bin/bash
# Run Tests Script
# Executes the test suite with proper environment setup

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

echo "Running RAG System Tests"
echo "======================"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "Error: pytest is not installed"
    echo "Installing test dependencies..."
    pip install pytest pytest-cov
fi

# Run tests
echo ""
echo "Running unit tests..."
pytest tests/ -m "not integration and not requires_ollama" -v

# Optionally run integration tests if requested
if [ "$1" == "--integration" ] || [ "$1" == "-i" ]; then
    if [ -z "$RUN_INTEGRATION_TESTS" ]; then
        echo ""
        echo "Warning: Integration tests require Ollama and models to be available"
        echo "Set RUN_INTEGRATION_TESTS=1 to run integration tests"
        echo "Skipping integration tests..."
    else
        echo ""
        echo "Running integration tests..."
        pytest tests/ -m "integration or requires_ollama" -v
    fi
fi

echo ""
echo "Test run complete!"
echo ""
echo "Coverage report generated in htmlcov/index.html"

