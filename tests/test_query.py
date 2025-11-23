"""
Unit tests for query.py module
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


class TestQueryDocs:
    """Test query_docs function."""
    
    @patch('query.ChatOllama')
    @patch('query.get_vector_db')
    @patch('query.MultiQueryRetriever')
    @patch('query.RetrievalQA')
    def test_query_success(self, mock_qa, mock_retriever, mock_get_db, mock_llm):
        """Test successful query processing."""
        # Setup mocks
        mock_db = Mock()
        mock_retriever_instance = Mock()
        mock_db.as_retriever.return_value = mock_retriever_instance
        mock_get_db.return_value = mock_db
        
        mock_llm_instance = Mock()
        mock_llm.return_value = mock_llm_instance
        
        mock_qa_instance = Mock()
        mock_qa.from_chain_type.return_value = mock_qa_instance
        
        # Mock query result
        mock_qa_instance.return_value = {
            'result': 'Test answer',
            'source_documents': [Mock(page_content='Source 1'), Mock(page_content='Source 2')]
        }
        mock_qa_instance.__call__ = Mock(return_value={
            'result': 'Test answer',
            'source_documents': [Mock(page_content='Source 1'), Mock(page_content='Source 2')]
        })
        
        from query import query_docs
        
        result = query_docs("Test question")
        
        assert result['result'] == 'Test answer'
        assert len(result['source_documents']) == 2
        assert result['query'] == "Test question"
    
    def test_query_empty_question(self):
        """Test query with empty question."""
        from query import query_docs
        
        with pytest.raises(ValueError, match="Question cannot be empty"):
            query_docs("")
        
        with pytest.raises(ValueError, match="Question cannot be empty"):
            query_docs("   ")
    
    @patch('query.ChatOllama')
    @patch('query.get_vector_db')
    def test_query_with_version(self, mock_get_db, mock_llm):
        """Test query with version parameter."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        with patch('query.MultiQueryRetriever') as mock_retriever, \
             patch('query.RetrievalQA') as mock_qa:
            
            mock_qa_instance = Mock()
            mock_qa.from_chain_type.return_value = mock_qa_instance
            mock_qa_instance.return_value = {
                'result': 'Answer',
                'source_documents': []
            }
            mock_qa_instance.__call__ = Mock(return_value={
                'result': 'Answer',
                'source_documents': []
            })
            
            from query import query_docs
            
            query_docs("Test", version="1.2.3")
            
            # Verify version was passed to get_vector_db
            mock_get_db.assert_called_once()
            call_kwargs = mock_get_db.call_args.kwargs
            assert call_kwargs.get('version') == "1.2.3"


class TestQuerySimple:
    """Test query_simple function."""
    
    @patch('query.ChatOllama')
    @patch('query.get_vector_db')
    @patch('query.RetrievalQA')
    def test_simple_query_success(self, mock_qa, mock_get_db, mock_llm):
        """Test successful simple query."""
        mock_db = Mock()
        mock_retriever = Mock()
        mock_db.as_retriever.return_value = mock_retriever
        mock_get_db.return_value = mock_db
        
        mock_qa_instance = Mock()
        mock_qa.from_chain_type.return_value = mock_qa_instance
        mock_qa_instance.return_value = {
            'result': 'Simple answer',
            'source_documents': []
        }
        mock_qa_instance.__call__ = Mock(return_value={
            'result': 'Simple answer',
            'source_documents': []
        })
        
        from query import query_simple
        
        result = query_simple("Test question")
        
        assert result['result'] == 'Simple answer'
        # Simple query should not use MultiQueryRetriever
        mock_qa.from_chain_type.assert_called_once()


class TestQueryParameters:
    """Test query parameter handling."""
    
    @patch('query.query_docs')
    def test_query_with_k_parameter(self, mock_query):
        """Test query with custom k parameter."""
        mock_query.return_value = {
            'result': 'Answer',
            'source_documents': [],
            'query': 'Test'
        }
        
        from query import query_docs
        
        query_docs("Test", k=5)
        
        # Verify k parameter is used in retriever
        mock_query.assert_called_once()
    
    def test_query_empty_result_handling(self):
        """Test handling of empty query results."""
        from query import query_docs
        
        with patch('query.ChatOllama'), \
             patch('query.get_vector_db'), \
             patch('query.MultiQueryRetriever'), \
             patch('query.RetrievalQA') as mock_qa:
            
            mock_qa_instance = Mock()
            mock_qa.from_chain_type.return_value = mock_qa_instance
            mock_qa_instance.return_value = {
                'result': '',
                'source_documents': []
            }
            mock_qa_instance.__call__ = Mock(return_value={
                'result': '',
                'source_documents': []
            })
            
            result = query_docs("Test question")
            
            # Should handle empty results gracefully
            assert result['result'] == ''
            assert len(result['source_documents']) == 0

