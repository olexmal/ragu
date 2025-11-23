"""
Vector Database Module
Initializes and manages ChromaDB connection with version-aware collections.
"""
import os
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CHROMA_PATH = os.getenv('CHROMA_PATH', 'chroma')
COLLECTION_NAME = os.getenv('COLLECTION_NAME', 'common-model-docs')
TEXT_EMBEDDING_MODEL = os.getenv('TEXT_EMBEDDING_MODEL', 'nomic-embed-text')


def get_vector_db(collection_name=None, version=None):
    """
    Get or create a ChromaDB instance.
    
    Args:
        collection_name: Name of the collection (defaults to COLLECTION_NAME)
        version: Optional version string for version-specific collections
        
    Returns:
        Chroma: ChromaDB instance
    """
    # Determine final collection name
    if version:
        final_collection_name = f"{collection_name or COLLECTION_NAME}-v{version}"
    else:
        final_collection_name = collection_name or COLLECTION_NAME
    
    # Initialize embedding function
    embedding = OllamaEmbeddings(
        model=TEXT_EMBEDDING_MODEL
    )
    
    # Create or load ChromaDB instance
    db = Chroma(
        collection_name=final_collection_name,
        persist_directory=CHROMA_PATH,
        embedding_function=embedding
    )
    
    return db


def get_or_create_collection(collection_name, embedding_function, version=None):
    """
    Get existing collection or return None if it doesn't exist.
    
    Args:
        collection_name: Name of the collection
        embedding_function: Embedding function to use
        version: Optional version string
        
    Returns:
        tuple: (Chroma instance or None, bool indicating if collection exists)
    """
    # Determine final collection name
    if version:
        final_collection_name = f"{collection_name}-v{version}"
    else:
        final_collection_name = collection_name
    
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
        return db, True  # Collection exists
    except Exception:
        # Collection doesn't exist
        return None, False

