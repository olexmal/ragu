"""
Unit tests for utils.py module
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, Mock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


class TestMavenVersion:
    """Test Maven version resolution."""
    
    @patch('utils.subprocess.run')
    def test_get_maven_version_success(self, mock_run):
        """Test successful Maven version resolution."""
        mock_run.return_value = Mock(returncode=0, stdout="1.2.3\n")
        
        from utils import get_maven_version
        
        version = get_maven_version()
        assert version == "1.2.3"
    
    @patch('utils.subprocess.run')
    def test_get_maven_version_failure(self, mock_run):
        """Test Maven version resolution failure."""
        mock_run.return_value = Mock(returncode=1, stdout="")
        
        from utils import get_maven_version
        
        version = get_maven_version()
        assert version is None
    
    @patch('utils.subprocess.run')
    def test_get_maven_version_empty(self, mock_run):
        """Test Maven version resolution with empty output."""
        mock_run.return_value = Mock(returncode=0, stdout="\n")
        
        from utils import get_maven_version
        
        version = get_maven_version()
        assert version is None


class TestVersionExtraction:
    """Test version extraction from paths."""
    
    def test_extract_version_from_path(self):
        """Test extracting version from file path."""
        from utils import extract_version_from_path
        
        assert extract_version_from_path("common-model-v1.2.3") == "1.2.3"
        assert extract_version_from_path("version-1.2.3") == "1.2.3"
        assert extract_version_from_path("v2.0.0") == "2.0.0"
        assert extract_version_from_path("1.2.3") == "1.2.3"
        assert extract_version_from_path("no-version") is None


class TestCollectionNaming:
    """Test collection name generation."""
    
    def test_generate_collection_name_with_version(self):
        """Test generating collection name with version."""
        from utils import generate_collection_name
        
        name = generate_collection_name("test-collection", "1.2.3")
        assert name == "test-collection-v1.2.3"
    
    def test_generate_collection_name_without_version(self):
        """Test generating collection name without version."""
        from utils import generate_collection_name
        
        name = generate_collection_name("test-collection")
        assert name == "test-collection"

