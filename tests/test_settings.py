"""
Unit tests for settings.py module
"""
import pytest
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


class TestConfluenceSettings:
    """Test Confluence settings storage."""
    
    @pytest.fixture
    def temp_settings_dir(self):
        """Create a temporary directory for settings files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('settings.SETTINGS_DIR', Path(tmpdir)):
                with patch('settings.CONFLUENCE_SETTINGS_FILE', Path(tmpdir) / 'confluence.json'):
                    yield tmpdir
    
    def test_get_confluence_settings_defaults(self, temp_settings_dir):
        """Test getting default settings when file doesn't exist."""
        from settings import get_confluence_settings
        
        settings = get_confluence_settings()
        
        assert settings['enabled'] is False
        assert settings['url'] == ""
        assert settings['instance_type'] == "cloud"
        assert settings['api_token'] == ""
        assert settings['username'] == ""
        assert settings['password'] == ""
        assert settings['page_ids'] == []
        assert settings['auto_sync'] is False
        assert settings['sync_interval'] == 3600
    
    def test_get_confluence_settings_existing(self, temp_settings_dir):
        """Test loading existing settings from file."""
        from settings import get_confluence_settings, CONFLUENCE_SETTINGS_FILE
        
        test_settings = {
            "enabled": True,
            "url": "https://test.atlassian.net",
            "instance_type": "cloud",
            "api_token": "test-token",
            "page_ids": ["123", "456"],
            "auto_sync": True,
            "sync_interval": 7200
        }
        
        CONFLUENCE_SETTINGS_FILE.write_text(json.dumps(test_settings))
        
        settings = get_confluence_settings()
        
        assert settings['enabled'] is True
        assert settings['url'] == "https://test.atlassian.net"
        assert settings['api_token'] == "test-token"
        assert settings['page_ids'] == ["123", "456"]
        assert settings['auto_sync'] is True
        assert settings['sync_interval'] == 7200
    
    def test_get_confluence_settings_partial(self, temp_settings_dir):
        """Test loading settings with missing keys (should merge with defaults)."""
        from settings import get_confluence_settings, CONFLUENCE_SETTINGS_FILE
        
        partial_settings = {
            "url": "https://test.atlassian.net",
            "instance_type": "server"
        }
        
        CONFLUENCE_SETTINGS_FILE.write_text(json.dumps(partial_settings))
        
        settings = get_confluence_settings()
        
        # Should have provided values
        assert settings['url'] == "https://test.atlassian.net"
        assert settings['instance_type'] == "server"
        # Should have defaults for missing keys
        assert settings['enabled'] is False
        assert settings['page_ids'] == []
        assert settings['auto_sync'] is False
    
    def test_get_confluence_settings_invalid_json(self, temp_settings_dir):
        """Test handling invalid JSON in settings file."""
        from settings import get_confluence_settings, CONFLUENCE_SETTINGS_FILE
        
        CONFLUENCE_SETTINGS_FILE.write_text("invalid json content")
        
        # Should return defaults on error
        settings = get_confluence_settings()
        
        assert settings['enabled'] is False
        assert settings['url'] == ""
    
    def test_save_confluence_settings_success(self, temp_settings_dir):
        """Test successfully saving settings."""
        from settings import save_confluence_settings, get_confluence_settings, CONFLUENCE_SETTINGS_FILE
        
        test_settings = {
            "enabled": True,
            "url": "https://test.atlassian.net",
            "instance_type": "cloud",
            "api_token": "test-token",
            "username": "",
            "password": "",
            "page_ids": ["123", "456"],
            "auto_sync": True,
            "sync_interval": 7200
        }
        
        result = save_confluence_settings(test_settings)
        
        assert result is True
        assert CONFLUENCE_SETTINGS_FILE.exists()
        
        # Verify saved content
        saved_settings = get_confluence_settings()
        assert saved_settings['url'] == "https://test.atlassian.net"
        assert saved_settings['page_ids'] == ["123", "456"]
    
    def test_save_confluence_settings_merges_defaults(self, temp_settings_dir):
        """Test that saving merges with defaults for missing keys."""
        from settings import save_confluence_settings, get_confluence_settings
        
        partial_settings = {
            "url": "https://test.atlassian.net",
            "instance_type": "server"
        }
        
        save_confluence_settings(partial_settings)
        
        # Load and verify all keys are present
        settings = get_confluence_settings()
        assert settings['url'] == "https://test.atlassian.net"
        assert settings['instance_type'] == "server"
        assert 'enabled' in settings
        assert 'page_ids' in settings
        assert 'auto_sync' in settings
        assert 'sync_interval' in settings
    
    def test_save_confluence_settings_creates_directory(self, temp_settings_dir):
        """Test that save creates the settings directory if it doesn't exist."""
        from settings import save_confluence_settings, SETTINGS_DIR
        
        # Remove directory if it exists
        if SETTINGS_DIR.exists():
            import shutil
            shutil.rmtree(SETTINGS_DIR)
        
        test_settings = {
            "url": "https://test.atlassian.net",
            "instance_type": "cloud"
        }
        
        result = save_confluence_settings(test_settings)
        
        assert result is True
        assert SETTINGS_DIR.exists()

