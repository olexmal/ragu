"""
Document Embedding Module
Processes and embeds documentation into vector database with incremental update support.
"""
import os
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.document_loaders import UnstructuredHTMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
import time
from .get_vector_db import get_or_create_collection
from .utils import detect_document_format, extract_version_from_path, setup_logging
from .monitoring import get_embedding_monitor

load_dotenv()

CHROMA_PATH = os.getenv('CHROMA_PATH', 'chroma')
COLLECTION_NAME = os.getenv('COLLECTION_NAME', 'common-model-docs')
TEXT_EMBEDDING_MODEL = os.getenv('TEXT_EMBEDDING_MODEL', 'nomic-embed-text')

logger = setup_logging()


def get_or_create_collection_helper(collection_name, embedding_function, version=None):
    """
    Helper function to get or create collection.
    Wrapper around get_vector_db.get_or_create_collection for embed module.
    """
    return get_or_create_collection(collection_name, embedding_function, version)


def embed_file(file_path, collection_name=None, version=None, overwrite=False):
    """
    Embed a file into ChromaDB with support for incremental updates.
    
    Args:
        file_path: Path to the file to embed
        collection_name: Name of the collection (defaults to COLLECTION_NAME)
        version: Optional version string for version-specific collections
        overwrite: If True, delete existing collection before embedding
        
    Returns:
        Chroma: ChromaDB instance
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Determine collection name
    if version:
        final_collection_name = f"{collection_name or COLLECTION_NAME}-v{version}"
    else:
        final_collection_name = collection_name or COLLECTION_NAME
    
    logger.info(f"Embedding file: {file_path} into collection: {final_collection_name}")
    start_time = time.time()
    
    # Detect document format and load
    doc_format = detect_document_format(str(file_path))
    
    if doc_format == 'pdf':
        loader = PyPDFLoader(str(file_path))
    elif doc_format == 'html':
        loader = UnstructuredHTMLLoader(str(file_path))
    elif doc_format in ['txt', 'md']:
        loader = TextLoader(str(file_path))
    else:
        raise ValueError(f"Unsupported document format: {doc_format}")
    
    documents = loader.load()
    logger.info(f"Loaded {len(documents)} documents from {file_path}")
    
    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_documents(documents)
    logger.info(f"Split into {len(chunks)} chunks")
    
    # Add metadata to chunks
    for chunk in chunks:
        chunk.metadata = chunk.metadata or {}
        chunk.metadata['source_file'] = str(file_path)
        chunk.metadata['file_format'] = doc_format
        if version:
            chunk.metadata['version'] = version
        else:
            # Try to extract version from path
            extracted_version = extract_version_from_path(str(file_path))
            if extracted_version:
                chunk.metadata['version'] = extracted_version
    
    # Create embeddings
    embedding = OllamaEmbeddings(
        model=TEXT_EMBEDDING_MODEL
    )
    
    # Handle collection creation or update
    if overwrite:
        logger.info(f"Overwrite mode: deleting existing collection {final_collection_name}")
        # Delete existing collection if it exists
        try:
            existing_db = Chroma(
                collection_name=final_collection_name,
                persist_directory=CHROMA_PATH,
                embedding_function=embedding
            )
            existing_db.delete_collection()
            logger.info(f"Deleted existing collection: {final_collection_name}")
        except Exception as e:
            logger.debug(f"Collection {final_collection_name} does not exist or error deleting: {e}")
        
        # After deletion, always create new collection
        db = Chroma.from_documents(
            chunks,
            embedding,
            collection_name=final_collection_name,
            persist_directory=CHROMA_PATH
        )
        logger.info(f"Created new collection: {final_collection_name} with {len(chunks)} chunks")
    else:
        # Check if collection exists for incremental update
        db, collection_exists = get_or_create_collection_helper(
            final_collection_name, 
            embedding, 
            version
        )
        
        if collection_exists:
            # Incremental update: add documents to existing collection
            # This preserves all existing documents and appends new ones
            logger.info(f"Incremental update: adding {len(chunks)} chunks to existing collection")
            db.add_documents(chunks)
            logger.info(f"Added {len(chunks)} chunks to collection: {final_collection_name}")
        else:
            # Create new collection with documents
            logger.info(f"Creating new collection: {final_collection_name}")
            db = Chroma.from_documents(
                chunks,
                embedding,
                collection_name=final_collection_name,
                persist_directory=CHROMA_PATH
            )
            logger.info(f"Created new collection: {final_collection_name} with {len(chunks)} chunks")
    
    # Log to monitoring
    duration = time.time() - start_time
    monitor = get_embedding_monitor()
    monitor.log_embedding(
        str(file_path),
        version=version,
        collection_name=final_collection_name,
        chunk_count=len(chunks),
        duration=duration,
        success=True
    )
    
    return db


def embed_directory(directory_path, collection_name=None, version=None, overwrite=False, file_extensions=None):
    """
    Embed all supported files from a directory.
    
    Args:
        directory_path: Path to the directory
        collection_name: Name of the collection
        version: Optional version string
        overwrite: If True, delete existing collection before embedding
        file_extensions: List of file extensions to process (default: ['.pdf', '.html', '.txt', '.md'])
        
    Returns:
        dict: Summary of embedding operations
    """
    if file_extensions is None:
        file_extensions = ['.pdf', '.html', '.htm', '.txt', '.md']
    
    directory_path = Path(directory_path)
    if not directory_path.is_dir():
        raise ValueError(f"Not a directory: {directory_path}")
    
    files = []
    for ext in file_extensions:
        files.extend(directory_path.rglob(f'*{ext}'))
    
    logger.info(f"Found {len(files)} files to embed in {directory_path}")
    
    results = {
        'success': 0,
        'failed': 0,
        'errors': []
    }
    
    for file_path in files:
        try:
            embed_file(str(file_path), collection_name, version, overwrite=False)  # Always incremental for batch
            results['success'] += 1
        except Exception as e:
            logger.error(f"Failed to embed {file_path}: {e}")
            results['failed'] += 1
            results['errors'].append({'file': str(file_path), 'error': str(e)})
    
    logger.info(f"Embedding complete: {results['success']} succeeded, {results['failed']} failed")
    return results

