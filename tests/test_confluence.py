"""
Unit tests for confluence.py module
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


class TestConfluenceIntegration:
    """Test ConfluenceIntegration class."""
    
    @patch('confluence.ConfluenceCloud')
    def test_init_cloud_with_token(self, mock_confluence_cloud):
        """Test initializing Confluence Cloud with API token."""
        from confluence import ConfluenceIntegration
        
        mock_instance = Mock()
        mock_confluence_cloud.return_value = mock_instance
        
        integration = ConfluenceIntegration(
            url="https://test.atlassian.net",
            instance_type="cloud",
            api_token="test-token"
        )
        
        assert integration.url == "https://test.atlassian.net"
        assert integration.instance_type == "cloud"
        assert integration.api_token == "test-token"
        mock_confluence_cloud.assert_called_once_with(
            url="https://test.atlassian.net",
            token="test-token"
        )
    
    @patch('confluence.ConfluenceCloud')
    def test_init_cloud_with_username_password(self, mock_confluence_cloud):
        """Test initializing Confluence Cloud with username and password."""
        from confluence import ConfluenceIntegration
        
        mock_instance = Mock()
        mock_confluence_cloud.return_value = mock_instance
        
        integration = ConfluenceIntegration(
            url="https://test.atlassian.net",
            instance_type="cloud",
            username="user@example.com",
            password="api-token"
        )
        
        mock_confluence_cloud.assert_called_once_with(
            url="https://test.atlassian.net",
            username="user@example.com",
            password="api-token",
            cloud=True
        )
    
    @patch('confluence.Confluence')
    def test_init_server_with_token(self, mock_confluence):
        """Test initializing Confluence Server with token."""
        from confluence import ConfluenceIntegration
        
        mock_instance = Mock()
        mock_confluence.return_value = mock_instance
        
        integration = ConfluenceIntegration(
            url="https://confluence.example.com",
            instance_type="server",
            api_token="test-token"
        )
        
        assert integration.instance_type == "server"
        mock_confluence.assert_called_once_with(
            url="https://confluence.example.com",
            token="test-token"
        )
    
    @patch('confluence.Confluence')
    def test_init_server_with_username_password(self, mock_confluence):
        """Test initializing Confluence Server with username and password."""
        from confluence import ConfluenceIntegration
        
        mock_instance = Mock()
        mock_confluence.return_value = mock_instance
        
        integration = ConfluenceIntegration(
            url="https://confluence.example.com",
            instance_type="server",
            username="admin",
            password="password"
        )
        
        mock_confluence.assert_called_once_with(
            url="https://confluence.example.com",
            username="admin",
            password="password"
        )
    
    def test_init_missing_credentials_cloud(self):
        """Test initialization fails when credentials are missing for Cloud."""
        from confluence import ConfluenceIntegration
        
        with pytest.raises(ValueError, match="Cloud instance requires"):
            ConfluenceIntegration(
                url="https://test.atlassian.net",
                instance_type="cloud"
            )
    
    def test_init_missing_credentials_server(self):
        """Test initialization fails when credentials are missing for Server."""
        from confluence import ConfluenceIntegration
        
        with pytest.raises(ValueError, match="Server instance requires"):
            ConfluenceIntegration(
                url="https://confluence.example.com",
                instance_type="server"
            )
    
    @patch('confluence.ConfluenceCloud')
    def test_url_normalization(self, mock_confluence_cloud):
        """Test that URL is normalized (trailing slash removed)."""
        from confluence import ConfluenceIntegration
        
        mock_instance = Mock()
        mock_confluence_cloud.return_value = mock_instance
        
        integration = ConfluenceIntegration(
            url="https://test.atlassian.net/",
            instance_type="cloud",
            api_token="test-token"
        )
        
        assert integration.url == "https://test.atlassian.net"
    
    @patch('confluence.ConfluenceCloud')
    def test_extract_page_id_from_url(self, mock_confluence_cloud):
        """Test extracting page ID from various URL formats."""
        from confluence import ConfluenceIntegration
        
        mock_instance = Mock()
        mock_confluence_cloud.return_value = mock_instance
        
        integration = ConfluenceIntegration(
            url="https://test.atlassian.net",
            instance_type="cloud",
            api_token="test-token"
        )
        
        # Test numeric ID
        assert integration.extract_page_id_from_url("123456") == "123456"
        
        # Test URL with pageId parameter
        assert integration.extract_page_id_from_url("https://test.atlassian.net/pages/viewpage.action?pageId=123456") == "123456"
        
        # Test URL with /pages/ path
        assert integration.extract_page_id_from_url("https://test.atlassian.net/spaces/SPACE/pages/123456/Title") == "123456"
        
        # Test invalid URL
        assert integration.extract_page_id_from_url("invalid-url") is None
    
    @patch('confluence.ConfluenceCloud')
    def test_fetch_page_success(self, mock_confluence_cloud):
        """Test successfully fetching a page."""
        from confluence import ConfluenceIntegration
        
        mock_instance = Mock()
        mock_page = {
            'id': '123456',
            'title': 'Test Page',
            'body': {
                'storage': {
                    'value': '<p>Test content</p>'
                }
            },
            'space': {'key': 'TEST', 'name': 'Test Space'},
            'version': {'number': 1}
        }
        mock_instance.get_page_by_id.return_value = mock_page
        mock_confluence_cloud.return_value = mock_instance
        
        integration = ConfluenceIntegration(
            url="https://test.atlassian.net",
            instance_type="cloud",
            api_token="test-token"
        )
        
        result = integration.fetch_page("123456")
        
        assert result == mock_page
        mock_instance.get_page_by_id.assert_called_once_with(
            page_id="123456",
            expand="body.storage,space,version"
        )
    
    @patch('confluence.ConfluenceCloud')
    def test_fetch_page_not_found(self, mock_confluence_cloud):
        """Test fetching a non-existent page."""
        from confluence import ConfluenceIntegration
        
        mock_instance = Mock()
        mock_instance.get_page_by_id.return_value = None
        mock_confluence_cloud.return_value = mock_instance
        
        integration = ConfluenceIntegration(
            url="https://test.atlassian.net",
            instance_type="cloud",
            api_token="test-token"
        )
        
        result = integration.fetch_page("999999")
        
        assert result is None
    
    @patch('confluence.ConfluenceCloud')
    def test_fetch_page_exception(self, mock_confluence_cloud):
        """Test handling exceptions when fetching a page."""
        from confluence import ConfluenceIntegration
        
        mock_instance = Mock()
        mock_instance.get_page_by_id.side_effect = Exception("API Error")
        mock_confluence_cloud.return_value = mock_instance
        
        integration = ConfluenceIntegration(
            url="https://test.atlassian.net",
            instance_type="cloud",
            api_token="test-token"
        )
        
        result = integration.fetch_page("123456")
        
        assert result is None
    
    @patch('confluence.ConfluenceCloud')
    def test_fetch_pages_multiple(self, mock_confluence_cloud):
        """Test fetching multiple pages."""
        from confluence import ConfluenceIntegration
        
        mock_instance = Mock()
        mock_page1 = {'id': '123', 'title': 'Page 1', 'body': {'storage': {'value': 'Content 1'}}}
        mock_page2 = {'id': '456', 'title': 'Page 2', 'body': {'storage': {'value': 'Content 2'}}}
        mock_instance.get_page_by_id.side_effect = [mock_page1, mock_page2]
        mock_confluence_cloud.return_value = mock_instance
        
        integration = ConfluenceIntegration(
            url="https://test.atlassian.net",
            instance_type="cloud",
            api_token="test-token"
        )
        
        results = integration.fetch_pages(["123", "456"])
        
        assert len(results) == 2
        assert results[0] == mock_page1
        assert results[1] == mock_page2
    
    @patch('confluence.ConfluenceCloud')
    def test_get_page_content_storage_format(self, mock_confluence_cloud):
        """Test extracting content from page with storage format."""
        from confluence import ConfluenceIntegration
        
        mock_instance = Mock()
        mock_confluence_cloud.return_value = mock_instance
        
        integration = ConfluenceIntegration(
            url="https://test.atlassian.net",
            instance_type="cloud",
            api_token="test-token"
        )
        
        page = {
            'body': {
                'storage': {
                    'value': '<p>Test <strong>content</strong> here</p>'
                }
            }
        }
        
        content = integration.get_page_content(page)
        
        assert 'Test' in content
        assert 'content' in content
        assert 'here' in content
        # HTML tags should be removed
        assert '<p>' not in content
        assert '<strong>' not in content
    
    @patch('confluence.ConfluenceCloud')
    def test_get_page_content_view_format(self, mock_confluence_cloud):
        """Test extracting content from page with view format."""
        from confluence import ConfluenceIntegration
        
        mock_instance = Mock()
        mock_confluence_cloud.return_value = mock_instance
        
        integration = ConfluenceIntegration(
            url="https://test.atlassian.net",
            instance_type="cloud",
            api_token="test-token"
        )
        
        page = {
            'body': {
                'view': {
                    'value': '<p>View format content</p>'
                }
            }
        }
        
        content = integration.get_page_content(page)
        
        assert 'View format content' in content
    
    @patch('confluence.ConfluenceCloud')
    def test_get_page_content_empty(self, mock_confluence_cloud):
        """Test extracting content from page with no body."""
        from confluence import ConfluenceIntegration
        
        mock_instance = Mock()
        mock_confluence_cloud.return_value = mock_instance
        
        integration = ConfluenceIntegration(
            url="https://test.atlassian.net",
            instance_type="cloud",
            api_token="test-token"
        )
        
        page = {'body': {}}
        
        content = integration.get_page_content(page)
        
        assert content == ""
    
    @patch('confluence.ConfluenceCloud')
    def test_get_page_metadata(self, mock_confluence_cloud):
        """Test extracting metadata from a page."""
        from confluence import ConfluenceIntegration
        
        mock_instance = Mock()
        mock_confluence_cloud.return_value = mock_instance
        
        integration = ConfluenceIntegration(
            url="https://test.atlassian.net",
            instance_type="cloud",
            api_token="test-token"
        )
        
        page = {
            'id': '123456',
            'title': 'Test Page',
            'space': {
                'key': 'TEST',
                'name': 'Test Space'
            },
            'version': {
                'number': 2
            }
        }
        
        metadata = integration.get_page_metadata(page)
        
        assert metadata['source'] == 'confluence'
        assert metadata['page_id'] == '123456'
        assert metadata['page_title'] == 'Test Page'
        assert metadata['space_key'] == 'TEST'
        assert metadata['space_name'] == 'Test Space'
        assert metadata['version'] == 2
        assert '123456' in metadata['url']
    
    @patch('confluence.ConfluenceCloud')
    def test_test_connection_success(self, mock_confluence_cloud):
        """Test successful connection test."""
        from confluence import ConfluenceIntegration
        
        mock_instance = Mock()
        mock_instance.get_all_spaces.return_value = {'results': [{'key': 'TEST'}]}
        mock_confluence_cloud.return_value = mock_instance
        
        integration = ConfluenceIntegration(
            url="https://test.atlassian.net",
            instance_type="cloud",
            api_token="test-token"
        )
        
        result = integration.test_connection()
        
        assert result['success'] is True
        assert 'successful' in result['message'].lower()
    
    @patch('confluence.ConfluenceCloud')
    def test_test_connection_failure(self, mock_confluence_cloud):
        """Test failed connection test."""
        from confluence import ConfluenceIntegration
        
        mock_instance = Mock()
        mock_instance.get_all_spaces.side_effect = Exception("Authentication failed")
        mock_confluence_cloud.return_value = mock_instance
        
        integration = ConfluenceIntegration(
            url="https://test.atlassian.net",
            instance_type="cloud",
            api_token="test-token"
        )
        
        result = integration.test_connection()
        
        assert result['success'] is False
        assert 'failed' in result['message'].lower()
    
    @patch('confluence.Confluence')
    def test_test_connection_server(self, mock_confluence):
        """Test connection test for Server instance."""
        from confluence import ConfluenceIntegration
        
        mock_instance = Mock()
        mock_instance.get_all_spaces.return_value = {'results': [{'key': 'TEST'}]}
        mock_confluence.return_value = mock_instance
        
        integration = ConfluenceIntegration(
            url="https://confluence.example.com",
            instance_type="server",
            username="admin",
            password="password"
        )
        
        result = integration.test_connection()
        
        assert result['success'] is True
        assert result['instance_type'] == 'server'

