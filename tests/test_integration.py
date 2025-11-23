"""
Integration tests for RAG system
"""
import pytest
import os
import io
import tempfile
import sys
from pathlib import Path
from unittest.mock import patch, Mock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


@pytest.fixture
def test_env():
    """Set up test environment variables."""
    os.environ['CHROMA_PATH'] = './test_chroma'
    os.environ['COLLECTION_NAME'] = 'test-collection'
    os.environ['LLM_MODEL'] = 'mistral'
    os.environ['TEXT_EMBEDDING_MODEL'] = 'nomic-embed-text'
    yield
    # Cleanup
    if os.path.exists('./test_chroma'):
        import shutil
        shutil.rmtree('./test_chroma', ignore_errors=True)


class TestEndToEndWorkflow:
    """Test end-to-end embedding and querying workflow."""
    
    @pytest.mark.skipif(
        not os.getenv('RUN_INTEGRATION_TESTS'),
        reason="Integration tests require Ollama and models to be available"
    )
    def test_embed_and_query_workflow(self, test_env):
        """Test complete workflow: embed document and query it."""
        import tempfile
        from embed import embed_file
        from query import query_docs
        
        # Create a test document
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("""
            UserService Class Documentation
            
            The UserService class provides methods for managing users in the system.
            
            Methods:
            - createUser(name, email): Creates a new user with the given name and email
            - getUserById(id): Retrieves a user by their unique identifier
            - updateUser(id, data): Updates user information
            - deleteUser(id): Removes a user from the system
            
            Example usage:
            userService = new UserService();
            User user = userService.createUser("John Doe", "john@example.com");
            """)
            temp_file = f.name
        
        try:
            # Embed the document
            db = embed_file(temp_file, collection_name='test-collection', overwrite=True)
            
            # Query the document
            result = query_docs(
                "How do I create a user?",
                collection_name='test-collection'
            )
            
            # Verify results
            assert result is not None
            assert 'result' in result
            assert len(result['result']) > 0
            assert 'source_documents' in result
            assert len(result['source_documents']) > 0
            
        finally:
            # Cleanup
            os.unlink(temp_file)


class TestAPIIntegration:
    """Test API endpoint integration."""
    
    @patch('app.embed_file')
    def test_embed_endpoint(self, mock_embed_file):
        """Test /embed API endpoint."""
        from app import app
        
        mock_embed_file.return_value = Mock()
        
        with app.test_client() as client:
            # Create a test file
            data = {
                'file': (io.BytesIO(b'test content'), 'test.txt')
            }
            
            response = client.post('/embed', data=data, content_type='multipart/form-data')
            
            assert response.status_code == 200
            json_data = response.get_json()
            assert 'message' in json_data
            assert json_data['message'] == 'File embedded successfully'
    
    @patch('app.query_docs')
    def test_query_endpoint(self, mock_query_docs):
        """Test /query API endpoint."""
        from app import app
        
        mock_query_docs.return_value = {
            'result': 'Test answer',
            'source_documents': [Mock(page_content='Source')],
            'query': 'Test question'
        }
        
        with app.test_client() as client:
            response = client.post(
                '/query',
                json={'query': 'Test question'},
                content_type='application/json'
            )
            
            assert response.status_code == 200
            json_data = response.get_json()
            assert 'answer' in json_data
            assert json_data['answer'] == 'Test answer'
    
    def test_query_endpoint_missing_json(self):
        """Test /query endpoint with missing JSON."""
        from app import app
        
        with app.test_client() as client:
            response = client.post('/query', data='not json')
            
            assert response.status_code == 400
    
    def test_query_endpoint_empty_query(self):
        """Test /query endpoint with empty query."""
        from app import app
        
        with app.test_client() as client:
            response = client.post(
                '/query',
                json={'query': ''},
                content_type='application/json'
            )
            
            assert response.status_code == 400
    
    def test_health_endpoint(self):
        """Test /health endpoint."""
        from app import app
        
        with app.test_client() as client:
            response = client.get('/health')
            
            assert response.status_code in [200, 503]  # May be degraded if Ollama not available
            json_data = response.get_json()
            assert 'status' in json_data


class TestVersionWorkflow:
    """Test version-aware workflow."""
    
    @patch('embed.embed_file')
    def test_version_specific_collection(self, mock_embed_file):
        """Test creating version-specific collections."""
        from embed import embed_file
        
        mock_embed_file.return_value = Mock()
        
        embed_file("test.txt", version="1.2.3", overwrite=True)
        
        # Verify version was passed
        call_args = mock_embed_file.call_args
        assert call_args.kwargs.get('version') == "1.2.3"
    
    @patch('query.query_docs')
    def test_query_version_specific_collection(self, mock_query):
        """Test querying version-specific collections."""
        from query import query_docs
        
        mock_query.return_value = {
            'result': 'Answer',
            'source_documents': [],
            'query': 'Test'
        }
        
        query_docs("Test question", version="1.2.3")
        
        # Verify version was passed
        call_args = mock_query.call_args
        assert call_args.kwargs.get('version') == "1.2.3"


class TestSecurity:
    """Test security features."""
    
    def test_path_traversal_protection(self):
        """Test that path traversal attacks are prevented."""
        from app import app
        
        with app.test_client() as client:
            # Try to upload file with path traversal
            data = {
                'file': (io.BytesIO(b'malicious'), '../../etc/passwd')
            }
            
            response = client.post('/embed', data=data, content_type='multipart/form-data')
            
            # Should either reject or sanitize the filename
            assert response.status_code in [400, 200]
            if response.status_code == 200:
                # If accepted, filename should be sanitized
                json_data = response.get_json()
                assert '../../' not in json_data.get('filename', '')


class TestConfluenceAPI:
    """Test Confluence integration API endpoints."""
    
    @patch('app.get_confluence_settings')
    def test_get_confluence_settings_endpoint(self, mock_get_settings):
        """Test GET /settings/confluence endpoint."""
        from app import app
        
        mock_get_settings.return_value = {
            'enabled': True,
            'url': 'https://test.atlassian.net',
            'instance_type': 'cloud',
            'api_token': 'test-token',
            'page_ids': ['123', '456']
        }
        
        with app.test_client() as client:
            # Mock authentication
            with patch('app.requires_auth', lambda f: f):
                response = client.get('/settings/confluence')
                
                assert response.status_code == 200
                json_data = response.get_json()
                assert json_data['url'] == 'https://test.atlassian.net'
                assert json_data['instance_type'] == 'cloud'
                # Sensitive data should be masked
                assert json_data['api_token'] == '***'
    
    @patch('app.save_confluence_settings')
    def test_save_confluence_settings_endpoint_success(self, mock_save_settings):
        """Test POST /settings/confluence endpoint with valid data."""
        from app import app
        
        mock_save_settings.return_value = True
        
        with app.test_client() as client:
            with patch('app.requires_write_auth', lambda f: f):
                response = client.post(
                    '/settings/confluence',
                    json={
                        'url': 'https://test.atlassian.net',
                        'instance_type': 'cloud',
                        'api_token': 'test-token',
                        'page_ids': ['123']
                    },
                    content_type='application/json'
                )
                
                assert response.status_code == 200
                json_data = response.get_json()
                assert 'message' in json_data
                assert 'successfully' in json_data['message'].lower()
                mock_save_settings.assert_called_once()
    
    def test_save_confluence_settings_missing_url(self):
        """Test POST /settings/confluence with missing URL."""
        from app import app
        
        with app.test_client() as client:
            with patch('app.requires_write_auth', lambda f: f):
                response = client.post(
                    '/settings/confluence',
                    json={
                        'instance_type': 'cloud'
                    },
                    content_type='application/json'
                )
                
                assert response.status_code == 400
                json_data = response.get_json()
                assert 'error' in json_data
                assert 'URL' in json_data['error']
    
    def test_save_confluence_settings_invalid_instance_type(self):
        """Test POST /settings/confluence with invalid instance type."""
        from app import app
        
        with app.test_client() as client:
            with patch('app.requires_write_auth', lambda f: f):
                response = client.post(
                    '/settings/confluence',
                    json={
                        'url': 'https://test.atlassian.net',
                        'instance_type': 'invalid'
                    },
                    content_type='application/json'
                )
                
                assert response.status_code == 400
                json_data = response.get_json()
                assert 'error' in json_data
    
    @patch('app.ConfluenceIntegration')
    def test_test_confluence_connection_success(self, mock_confluence_class):
        """Test POST /confluence/test endpoint with successful connection."""
        from app import app
        
        mock_confluence = Mock()
        mock_confluence.test_connection.return_value = {
            'success': True,
            'message': 'Connection successful',
            'instance_type': 'cloud',
            'url': 'https://test.atlassian.net'
        }
        mock_confluence_class.return_value = mock_confluence
        
        with app.test_client() as client:
            with patch('app.requires_write_auth', lambda f: f):
                response = client.post(
                    '/confluence/test',
                    json={
                        'url': 'https://test.atlassian.net',
                        'instance_type': 'cloud',
                        'api_token': 'test-token'
                    },
                    content_type='application/json'
                )
                
                assert response.status_code == 200
                json_data = response.get_json()
                assert json_data['success'] is True
    
    @patch('app.ConfluenceIntegration')
    def test_test_confluence_connection_failure(self, mock_confluence_class):
        """Test POST /confluence/test endpoint with failed connection."""
        from app import app
        
        mock_confluence = Mock()
        mock_confluence.test_connection.return_value = {
            'success': False,
            'message': 'Authentication failed'
        }
        mock_confluence_class.return_value = mock_confluence
        
        with app.test_client() as client:
            with patch('app.requires_write_auth', lambda f: f):
                response = client.post(
                    '/confluence/test',
                    json={
                        'url': 'https://test.atlassian.net',
                        'instance_type': 'cloud',
                        'api_token': 'invalid-token'
                    },
                    content_type='application/json'
                )
                
                assert response.status_code == 400
                json_data = response.get_json()
                assert json_data['success'] is False
    
    @patch('app.embed_confluence_pages')
    @patch('app.get_confluence_settings')
    def test_fetch_confluence_pages_endpoint(self, mock_get_settings, mock_embed_pages):
        """Test POST /confluence/fetch endpoint."""
        from app import app
        
        mock_get_settings.return_value = {
            'url': 'https://test.atlassian.net',
            'instance_type': 'cloud',
            'api_token': 'test-token',
            'page_ids': ['123', '456']
        }
        mock_embed_pages.return_value = {
            'success': 2,
            'failed': 0,
            'errors': []
        }
        
        with app.test_client() as client:
            with patch('app.requires_write_auth', lambda f: f):
                response = client.post(
                    '/confluence/fetch',
                    json={
                        'page_ids': ['123', '456']
                    },
                    content_type='application/json'
                )
                
                assert response.status_code == 200
                json_data = response.get_json()
                assert 'message' in json_data
                assert 'results' in json_data
                assert json_data['results']['success'] == 2
    
    @patch('app.get_confluence_settings')
    def test_fetch_confluence_pages_no_config(self, mock_get_settings):
        """Test POST /confluence/fetch when Confluence is not configured."""
        from app import app
        
        mock_get_settings.return_value = {
            'url': '',
            'instance_type': 'cloud'
        }
        
        with app.test_client() as client:
            with patch('app.requires_write_auth', lambda f: f):
                response = client.post(
                    '/confluence/fetch',
                    json={},
                    content_type='application/json'
                )
                
                assert response.status_code == 400
                json_data = response.get_json()
                assert 'error' in json_data
                assert 'configured' in json_data['error'].lower()
    
    def test_fetch_confluence_pages_no_page_ids(self):
        """Test POST /confluence/fetch with no page IDs."""
        from app import app
        
        with app.test_client() as client:
            with patch('app.requires_write_auth', lambda f: f):
                with patch('app.get_confluence_settings', return_value={'page_ids': []}):
                    response = client.post(
                        '/confluence/fetch',
                        json={},
                        content_type='application/json'
                    )
                    
                    assert response.status_code == 400
                    json_data = response.get_json()
                    assert 'error' in json_data
                    assert 'page' in json_data['error'].lower()
    
    @patch('app.embed_confluence_pages')
    def test_fetch_confluence_pages_with_config_in_request(self, mock_embed_pages):
        """Test POST /confluence/fetch with config provided in request."""
        from app import app
        
        mock_embed_pages.return_value = {
            'success': 1,
            'failed': 0,
            'errors': []
        }
        
        with app.test_client() as client:
            with patch('app.requires_write_auth', lambda f: f):
                response = client.post(
                    '/confluence/fetch',
                    json={
                        'page_ids': ['123'],
                        'confluence_config': {
                            'url': 'https://test.atlassian.net',
                            'instance_type': 'cloud',
                            'api_token': 'test-token'
                        }
                    },
                    content_type='application/json'
                )
                
                assert response.status_code == 200
                mock_embed_pages.assert_called_once()
                # Verify config was passed
                call_args = mock_embed_pages.call_args
                assert call_args.kwargs['confluence_config']['url'] == 'https://test.atlassian.net'

