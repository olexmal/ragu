"""
Pytest configuration and shared fixtures
"""
import pytest
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


@pytest.fixture(scope="session")
def test_data_dir():
    """Return path to test data directory."""
    return Path(__file__).parent / "test_data"


@pytest.fixture(autouse=True)
def reset_env():
    """Reset environment variables before each test."""
    # Store original values
    original_env = {}
    env_vars = [
        'CHROMA_PATH',
        'COLLECTION_NAME',
        'LLM_MODEL',
        'TEXT_EMBEDDING_MODEL',
        'TEMP_FOLDER',
        'API_PORT',
        'API_HOST'
    ]
    
    for var in env_vars:
        original_env[var] = os.environ.get(var)
    
    yield
    
    # Restore original values
    for var, value in original_env.items():
        if value is None:
            os.environ.pop(var, None)
        else:
            os.environ[var] = value

