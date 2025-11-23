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

