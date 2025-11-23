"""
Unit tests for embed.py module
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from embed import embed_file, embed_directory, detect_document_format
from get_vector_db import get_vector_db


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_text_file(temp_dir):
    """Create a sample text file for testing."""
    file_path = Path(temp_dir) / "test.txt"
    file_path.write_text("This is a test document. " * 50)  # Create enough content
    return str(file_path)


@pytest.fixture
def sample_html_file(temp_dir):
    """Create a sample HTML file for testing."""
    file_path = Path(temp_dir) / "test.html"
    file_path.write_text("""
    <html>
    <body>
        <h1>Test Documentation</h1>
        <p>This is a test HTML document with some content.</p>
        <p>More content here for testing purposes.</p>
    </body>
    </html>
    """)
    return str(file_path)


class TestDocumentFormatDetection:
    """Test document format detection."""
    
    def test_detect_pdf(self):
        """Test PDF format detection."""
        from utils import detect_document_format
        assert detect_document_format("test.pdf") == "pdf"
    
    def test_detect_html(self):
        """Test HTML format detection."""
        from utils import detect_document_format
        assert detect_document_format("test.html") == "html"
        assert detect_document_format("test.htm") == "html"
    
    def test_detect_txt(self):
        """Test TXT format detection."""
        from utils import detect_document_format
        assert detect_document_format("test.txt") == "txt"
    
    def test_detect_markdown(self):
        """Test Markdown format detection."""
        from utils import detect_document_format
        assert detect_document_format("test.md") == "md"
        assert detect_document_format("test.markdown") == "md"
    
    def test_detect_unknown(self):
        """Test unknown format detection."""
        from utils import detect_document_format
        assert detect_document_format("test.xyz") == "unknown"


class TestEmbedFile:
    """Test embed_file function."""
    
    @patch('embed.OllamaEmbeddings')
    @patch('embed.Chroma')
    @patch('embed.PyPDFLoader')
    def test_embed_pdf_new_collection(self, mock_loader, mock_chroma, mock_embeddings, temp_dir):
        """Test embedding a PDF file into a new collection."""
        # Setup mocks
        mock_doc = Mock()
        mock_doc.page_content = "Test content"
        mock_doc.metadata = {}
        mock_loader_instance = Mock()
        mock_loader_instance.load.return_value = [mock_doc]
        mock_loader.return_value = mock_loader_instance
        
        mock_chroma_instance = Mock()
        mock_chroma.from_documents.return_value = mock_chroma_instance
        mock_chroma.return_value = mock_chroma_instance
        
        # Create a dummy PDF file
        pdf_path = Path(temp_dir) / "test.pdf"
        pdf_path.write_bytes(b"dummy pdf content")
        
        # Test
        result = embed_file(str(pdf_path), overwrite=False)
        
        # Verify
        mock_loader.assert_called_once()
        mock_chroma.from_documents.assert_called_once()
    
    @patch('embed.OllamaEmbeddings')
    @patch('embed.Chroma')
    @patch('embed.TextLoader')
    def test_embed_txt_incremental(self, mock_loader, mock_chroma, mock_embeddings, sample_text_file):
        """Test incremental embedding of a text file."""
        # Setup mocks
        mock_doc = Mock()
        mock_doc.page_content = "Test content"
        mock_doc.metadata = {}
        mock_loader_instance = Mock()
        mock_loader_instance.load.return_value = [mock_doc]
        mock_loader.return_value = mock_loader_instance
        
        # Mock existing collection
        mock_db = Mock()
        mock_db._collection.count.return_value = 5  # Collection exists
        mock_chroma_instance = Mock()
        mock_chroma.return_value = mock_db
        mock_chroma.from_documents.return_value = mock_chroma_instance
        
        # Mock get_or_create_collection to return existing collection
        with patch('embed.get_or_create_collection_helper', return_value=(mock_db, True)):
            result = embed_file(sample_text_file, overwrite=False)
            
            # Verify add_documents was called (incremental update)
            mock_db.add_documents.assert_called_once()
    
    def test_embed_file_not_found(self):
        """Test embedding a non-existent file."""
        with pytest.raises(FileNotFoundError):
            embed_file("/nonexistent/file.txt")
    
    def test_embed_file_unsupported_format(self, temp_dir):
        """Test embedding an unsupported file format."""
        file_path = Path(temp_dir) / "test.xyz"
        file_path.write_text("test content")
        
        with pytest.raises(ValueError, match="Unsupported document format"):
            embed_file(str(file_path))


class TestEmbedDirectory:
    """Test embed_directory function."""
    
    @patch('embed.embed_file')
    def test_embed_directory_success(self, mock_embed_file, temp_dir):
        """Test embedding a directory with multiple files."""
        # Create test files
        (Path(temp_dir) / "file1.txt").write_text("Content 1")
        (Path(temp_dir) / "file2.txt").write_text("Content 2")
        (Path(temp_dir) / "file3.md").write_text("Content 3")
        
        mock_embed_file.return_value = Mock()
        
        results = embed_directory(str(temp_dir))
        
        # Should have processed 3 files
        assert results['success'] == 3
        assert results['failed'] == 0
        assert mock_embed_file.call_count == 3
    
    def test_embed_directory_not_directory(self, temp_dir):
        """Test embedding a file path that's not a directory."""
        file_path = Path(temp_dir) / "notadir.txt"
        file_path.write_text("test")
        
        with pytest.raises(ValueError, match="Not a directory"):
            embed_directory(str(file_path))


class TestVersionHandling:
    """Test version handling in embedding."""
    
    @patch('embed.OllamaEmbeddings')
    @patch('embed.Chroma')
    @patch('embed.TextLoader')
    def test_embed_with_version(self, mock_loader, mock_chroma, mock_embeddings, sample_text_file):
        """Test embedding with version parameter."""
        mock_doc = Mock()
        mock_doc.page_content = "Test content"
        mock_doc.metadata = {}
        mock_loader_instance = Mock()
        mock_loader_instance.load.return_value = [mock_doc]
        mock_loader.return_value = mock_loader_instance
        
        mock_chroma_instance = Mock()
        mock_chroma.from_documents.return_value = mock_chroma_instance
        
        with patch('embed.get_or_create_collection_helper', return_value=(None, False)):
            result = embed_file(sample_text_file, version="1.2.3")
            
            # Verify collection name includes version
            call_args = mock_chroma.from_documents.call_args
            assert "1.2.3" in call_args.kwargs['collection_name']


class TestChunking:
    """Test text chunking functionality."""
    
    def test_chunking_large_document(self, temp_dir):
        """Test that large documents are properly chunked."""
        # Create a large text file
        large_content = "This is a test sentence. " * 1000  # ~25KB
        file_path = Path(temp_dir) / "large.txt"
        file_path.write_text(large_content)
        
        from langchain_community.document_loaders import TextLoader
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        loader = TextLoader(str(file_path))
        documents = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_documents(documents)
        
        # Should create multiple chunks
        assert len(chunks) > 1
        # Each chunk should be within reasonable size
        for chunk in chunks:
            assert len(chunk.page_content) <= 1200  # chunk_size + some margin


class TestConfluenceEmbedding:
    """Test Confluence page embedding functionality."""
    
    @patch('embed.ConfluenceIntegration')
    @patch('embed.OllamaEmbeddings')
    @patch('embed.Chroma')
    def test_embed_confluence_page_success(self, mock_chroma, mock_embeddings, mock_confluence_class):
        """Test successfully embedding a Confluence page."""
        from embed import embed_confluence_page
        
        # Mock Confluence integration
        mock_confluence = Mock()
        mock_page = {
            'id': '123456',
            'title': 'Test Page',
            'body': {
                'storage': {
                    'value': '<p>This is test content from Confluence page.</p>'
                }
            },
            'space': {'key': 'TEST', 'name': 'Test Space'},
            'version': {'number': 1}
        }
        mock_confluence.fetch_page.return_value = mock_page
        mock_confluence.get_page_content.return_value = 'This is test content from Confluence page.'
        mock_confluence.get_page_metadata.return_value = {
            'source': 'confluence',
            'page_id': '123456',
            'page_title': 'Test Page',
            'space_key': 'TEST',
            'space_name': 'Test Space',
            'version': 1,
            'url': 'https://test.atlassian.net/pages/viewpage.action?pageId=123456'
        }
        mock_confluence_class.return_value = mock_confluence
        
        # Mock Chroma
        mock_chroma_instance = Mock()
        mock_chroma.from_documents.return_value = mock_chroma_instance
        
        # Mock get_or_create_collection_helper
        with patch('embed.get_or_create_collection_helper', return_value=(None, False)):
            result = embed_confluence_page(
                page_id="123456",
                confluence_config={
                    'url': 'https://test.atlassian.net',
                    'instance_type': 'cloud',
                    'api_token': 'test-token'
                }
            )
            
            assert result == mock_chroma_instance
            mock_confluence.fetch_page.assert_called_once_with("123456", expand="body.storage,space,version")
            mock_chroma.from_documents.assert_called_once()
    
    @patch('embed.ConfluenceIntegration')
    def test_embed_confluence_page_not_found(self, mock_confluence_class):
        """Test embedding when page is not found."""
        from embed import embed_confluence_page
        
        mock_confluence = Mock()
        mock_confluence.fetch_page.return_value = None
        mock_confluence_class.return_value = mock_confluence
        
        with pytest.raises(ValueError, match="Failed to fetch"):
            embed_confluence_page(
                page_id="999999",
                confluence_config={
                    'url': 'https://test.atlassian.net',
                    'instance_type': 'cloud',
                    'api_token': 'test-token'
                }
            )
    
    @patch('embed.ConfluenceIntegration')
    def test_embed_confluence_page_no_content(self, mock_confluence_class):
        """Test embedding when page has no content."""
        from embed import embed_confluence_page
        
        mock_confluence = Mock()
        mock_page = {
            'id': '123456',
            'title': 'Empty Page',
            'body': {}
        }
        mock_confluence.fetch_page.return_value = mock_page
        mock_confluence.get_page_content.return_value = ""
        mock_confluence_class.return_value = mock_confluence
        
        with pytest.raises(ValueError, match="No content found"):
            embed_confluence_page(
                page_id="123456",
                confluence_config={
                    'url': 'https://test.atlassian.net',
                    'instance_type': 'cloud',
                    'api_token': 'test-token'
                }
            )
    
    @patch('embed.embed_confluence_page')
    def test_embed_confluence_pages_multiple(self, mock_embed_page):
        """Test embedding multiple Confluence pages."""
        from embed import embed_confluence_pages
        
        mock_db = Mock()
        mock_embed_page.return_value = mock_db
        
        confluence_config = {
            'url': 'https://test.atlassian.net',
            'instance_type': 'cloud',
            'api_token': 'test-token'
        }
        
        results = embed_confluence_pages(
            page_ids=["123", "456", "789"],
            confluence_config=confluence_config
        )
        
        assert results['success'] == 3
        assert results['failed'] == 0
        assert mock_embed_page.call_count == 3
    
    @patch('embed.embed_confluence_page')
    def test_embed_confluence_pages_with_failures(self, mock_embed_page):
        """Test embedding multiple pages with some failures."""
        from embed import embed_confluence_pages
        
        mock_db = Mock()
        # First succeeds, second fails, third succeeds
        mock_embed_page.side_effect = [mock_db, ValueError("Page not found"), mock_db]
        
        confluence_config = {
            'url': 'https://test.atlassian.net',
            'instance_type': 'cloud',
            'api_token': 'test-token'
        }
        
        results = embed_confluence_pages(
            page_ids=["123", "456", "789"],
            confluence_config=confluence_config
        )
        
        assert results['success'] == 2
        assert results['failed'] == 1
        assert len(results['errors']) == 1
        assert results['errors'][0]['page_id'] == "456"
    
    @patch('embed.ConfluenceIntegration')
    @patch('embed.OllamaEmbeddings')
    @patch('embed.Chroma')
    def test_embed_confluence_page_with_version(self, mock_chroma, mock_embeddings, mock_confluence_class):
        """Test embedding Confluence page with version."""
        from embed import embed_confluence_page
        
        mock_confluence = Mock()
        mock_page = {
            'id': '123456',
            'title': 'Test Page',
            'body': {'storage': {'value': '<p>Content</p>'}},
            'space': {'key': 'TEST'},
            'version': {'number': 1}
        }
        mock_confluence.fetch_page.return_value = mock_page
        mock_confluence.get_page_content.return_value = 'Content'
        mock_confluence.get_page_metadata.return_value = {
            'source': 'confluence',
            'page_id': '123456',
            'page_title': 'Test Page',
            'space_key': 'TEST'
        }
        mock_confluence_class.return_value = mock_confluence
        
        mock_chroma_instance = Mock()
        mock_chroma.from_documents.return_value = mock_chroma_instance
        
        with patch('embed.get_or_create_collection_helper', return_value=(None, False)):
            result = embed_confluence_page(
                page_id="123456",
                confluence_config={
                    'url': 'https://test.atlassian.net',
                    'instance_type': 'cloud',
                    'api_token': 'test-token'
                },
                version="1.2.3"
            )
            
            # Verify collection name includes version
            call_args = mock_chroma.from_documents.call_args
            assert "1.2.3" in call_args.kwargs['collection_name']

