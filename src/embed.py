"""
Document Embedding Module
Processes and embeds documentation into vector database with incremental update support.
"""
import os
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.document_loaders import UnstructuredHTMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.documents import Document
from dotenv import load_dotenv
import time
from typing import Dict, Any, Optional
from .get_vector_db import get_or_create_collection
from .utils import detect_document_format, extract_version_from_path, setup_logging
from .monitoring import get_embedding_monitor
from .confluence import ConfluenceIntegration
from .llm_providers import EmbeddingProviderFactory
from .settings import get_active_embedding_provider

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
    provider_config = get_active_embedding_provider()
    embedding = EmbeddingProviderFactory.get_embeddings(provider_config['type'], provider_config)
    
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


def embed_confluence_page(page_id: str, confluence_config: Dict[str, Any], 
                          collection_name=None, version=None, overwrite=False) -> Chroma:
    """
    Embed a Confluence page into ChromaDB.
    
    Args:
        page_id: Confluence page ID or URL
        confluence_config: Dictionary with Confluence configuration:
            - url: Confluence instance URL
            - instance_type: "cloud" or "server"
            - api_token: API token (optional)
            - username: Username (optional, for server or cloud)
            - password: Password or API token (optional)
        collection_name: Name of the collection (defaults to COLLECTION_NAME)
        version: Optional version string for version-specific collections
        overwrite: If True, delete existing collection before embedding
        
    Returns:
        Chroma: ChromaDB instance
    """
    # Initialize Confluence integration
    confluence = ConfluenceIntegration(
        url=confluence_config['url'],
        instance_type=confluence_config.get('instance_type', 'cloud'),
        api_token=confluence_config.get('api_token'),
        username=confluence_config.get('username'),
        password=confluence_config.get('password')
    )
    
    # Fetch the page with expanded content
    page = confluence.fetch_page(page_id, expand="body.storage,space,version")
    if not page:
        raise ValueError(f"Failed to fetch Confluence page: {page_id}")
    
    # Extract content and metadata
    content = confluence.get_page_content(page)
    metadata = confluence.get_page_metadata(page)
    
    if not content:
        raise ValueError(f"No content found in Confluence page: {page_id}")
    
    # Determine collection name
    if version:
        final_collection_name = f"{collection_name or COLLECTION_NAME}-v{version}"
    else:
        final_collection_name = collection_name or COLLECTION_NAME
    
    logger.info(f"Embedding Confluence page: {metadata.get('page_title', page_id)} into collection: {final_collection_name}")
    start_time = time.time()
    
    # Create Document object from Confluence content
    document = Document(
        page_content=content,
        metadata=metadata
    )
    
    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_documents([document])
    logger.info(f"Split into {len(chunks)} chunks")
    
    # Add version to metadata if provided
    if version:
        for chunk in chunks:
            chunk.metadata['version'] = version
    
    # Create embeddings
    provider_config = get_active_embedding_provider()
    embedding = EmbeddingProviderFactory.get_embeddings(provider_config['type'], provider_config)
    
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
        f"confluence:{page_id}",
        version=version,
        collection_name=final_collection_name,
        chunk_count=len(chunks),
        duration=duration,
        success=True
    )
    
    return db


def embed_confluence_pages(page_ids: list, confluence_config: Dict[str, Any],
                          collection_name=None, version=None, overwrite=False) -> Dict[str, Any]:
    """
    Embed multiple Confluence pages into ChromaDB.
    
    Args:
        page_ids: List of Confluence page IDs or URLs
        confluence_config: Dictionary with Confluence configuration
        collection_name: Name of the collection
        version: Optional version string
        overwrite: If True, delete existing collection before embedding
        
    Returns:
        dict: Summary of embedding operations
    """
    results = {
        'success': 0,
        'failed': 0,
        'errors': []
    }
    
    for page_id in page_ids:
        try:
            embed_confluence_page(
                page_id, 
                confluence_config, 
                collection_name, 
                version, 
                overwrite=False  # Always incremental for batch
            )
            results['success'] += 1
        except Exception as e:
            logger.error(f"Failed to embed Confluence page {page_id}: {e}")
            results['failed'] += 1
            results['errors'].append({'page_id': page_id, 'error': str(e)})
    
    logger.info(f"Confluence embedding complete: {results['success']} succeeded, {results['failed']} failed")
    return results

