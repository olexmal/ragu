"""
Vector Database Module
Initializes and manages ChromaDB connection with version-aware collections.
Implements connection pooling to reuse ChromaDB instances across requests.
"""
import os
import threading
from langchain_chroma import Chroma
from dotenv import load_dotenv
from .llm_providers import EmbeddingProviderFactory
from .settings import get_active_embedding_provider

# Load environment variables
load_dotenv()

CHROMA_PATH = os.getenv('CHROMA_PATH', 'chroma')
COLLECTION_NAME = os.getenv('COLLECTION_NAME', 'common-model-docs')
TEXT_EMBEDDING_MODEL = os.getenv('TEXT_EMBEDDING_MODEL', 'nomic-embed-text')

# Connection pool cache
_chroma_cache = {}
_cache_lock = threading.Lock()


def get_vector_db(collection_name=None, version=None):
    """
    Get or create a ChromaDB instance with connection pooling.
    Connections are cached and reused to improve performance.
    
    Args:
        collection_name: Name of the collection (defaults to COLLECTION_NAME)
        version: Optional version string for version-specific collections
        
    Returns:
        Chroma: ChromaDB instance (cached and reused)
    """
    # Determine final collection name (sanitize to meet ChromaDB requirements)
    from .utils import generate_collection_name
    base = collection_name or COLLECTION_NAME
    final_collection_name = generate_collection_name(base, version)
    
    # Use cache key for connection pooling
    cache_key = (final_collection_name, CHROMA_PATH)
    
    # Check cache first
    if cache_key in _chroma_cache:
        return _chroma_cache[cache_key]
    
    # Thread-safe connection creation
    with _cache_lock:
        # Double-check after acquiring lock (thread-safe singleton pattern)
        if cache_key in _chroma_cache:
            return _chroma_cache[cache_key]
        
        # Initialize embedding function
        provider_config = get_active_embedding_provider()
        embedding = EmbeddingProviderFactory.get_embeddings(provider_config['type'], provider_config)
        
        # Create or load ChromaDB instance
        db = Chroma(
            collection_name=final_collection_name,
            persist_directory=CHROMA_PATH,
            embedding_function=embedding
        )
        
        # Cache the connection
        _chroma_cache[cache_key] = db
        
        return db


def clear_connection_cache():
    """
    Clear the ChromaDB connection cache.
    Useful for testing or when connections need to be refreshed.
    """
    global _chroma_cache
    with _cache_lock:
        _chroma_cache.clear()


def get_or_create_collection(collection_name, embedding_function, version=None):
    """
    Get existing collection or return None if it doesn't exist.
    Uses connection pooling to cache and reuse connections.
    
    Args:
        collection_name: Name of the collection
        embedding_function: Embedding function to use
        version: Optional version string
        
    Returns:
        tuple: (Chroma instance or None, bool indicating if collection exists)
    """
    # Determine final collection name (sanitize to meet ChromaDB requirements)
    from .utils import generate_collection_name
    final_collection_name = generate_collection_name(collection_name, version)
    
    # Use cache key (note: embedding_function is part of the key since different
    # embedding functions would require different connections)
    # For simplicity, we'll use a hash of the embedding function or its type
    # In practice, embedding functions from the same provider/config are the same object
    cache_key = (final_collection_name, CHROMA_PATH, id(embedding_function))
    
    # Check cache first
    if cache_key in _chroma_cache:
        cached_db = _chroma_cache[cache_key]
        try:
            # Verify collection still exists
            _ = cached_db._collection.count()
            return cached_db, True
        except Exception:
            # Collection was deleted, remove from cache
            with _cache_lock:
                _chroma_cache.pop(cache_key, None)
    
    # Thread-safe connection creation
    with _cache_lock:
        # Double-check after acquiring lock
        if cache_key in _chroma_cache:
            cached_db = _chroma_cache[cache_key]
            try:
                _ = cached_db._collection.count()
                return cached_db, True
            except Exception:
                _chroma_cache.pop(cache_key, None)
        
        try:
            # Try to load existing collection
            db = Chroma(
                collection_name=final_collection_name,
                persist_directory=CHROMA_PATH,
                embedding_function=embedding_function
            )
            # Verify collection exists by checking if it has any documents
            # This will raise an error if collection doesn't exist
            _ = db._collection.count()
            # Cache the connection
            _chroma_cache[cache_key] = db
            return db, True  # Collection exists
        except Exception:
            # Collection doesn't exist
            return None, False

