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
from .settings import get_active_embedding_provider, get_confluence_settings

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


def import_confluence_page_to_vector_db(page_id: str, version: str = None, overwrite: bool = False) -> Dict[str, Any]:
    """
    Import a Confluence page to vector database using confluence-markdown-exporter.
    
    This function:
    1. Loads Confluence settings from settings storage
    2. Uses confluence-markdown-exporter to download the page as Markdown
    3. Saves Markdown to a temporary file
    4. Calls embed_file() to embed the Markdown content
    5. Cleans up the temporary file
    
    Args:
        page_id: Confluence page ID or URL (URLs will have page ID extracted)
        version: Optional version string for collection naming
        overwrite: If True, delete existing collection before embedding
        
    Returns:
        dict: Result dictionary with success status, message, and filename
    """
    import tempfile
    import subprocess
    import shutil
    
    # Validate page_id is a string
    if not isinstance(page_id, str):
        page_id = str(page_id)
    
    # Extract page ID from URL if needed
    if page_id.startswith('http'):
        # Extract page ID from Confluence URL
        # Format: https://domain.atlassian.net/wiki/spaces/SPACE/pages/PAGE_ID/...
        import re
        match = re.search(r'/pages/(\d+)', page_id)
        if match:
            page_id = match.group(1)
        else:
            raise ValueError(f"Could not extract page ID from URL: {page_id}")
    
    # Load Confluence settings
    settings = get_confluence_settings()
    if not settings.get('url'):
        raise ValueError("Confluence not configured. Please configure in Settings first.")
    
    # Initialize confluence-markdown-exporter
    # confluence-markdown-exporter typically requires:
    # - base_url: Confluence instance URL
    # - username: Username or email
    # - api_token: API token for authentication
    
    confluence_url = settings['url'].rstrip('/')
    
    # Extract username: use configured username, or extract from API token if it contains a colon (format: username:token)
    raw_api_token = settings.get('api_token', '')
    # Only extract username from token if token contains a colon and username wasn't explicitly set
    if ':' in raw_api_token and not settings.get('username'):
        username_from_token = raw_api_token.split(':', 1)[0]
    else:
        username_from_token = ''
    username = settings.get('username') or username_from_token
    
    # Extract API token - if we extracted username from api_token (meaning username wasn't explicitly set),
    # then extract just the token part (everything after the first colon)
    # Otherwise use the full api_token or fall back to password
    if ':' in raw_api_token and not settings.get('username'):
        # If api_token is in username:token format and username wasn't explicitly set,
        # extract just the token part (everything after the first colon)
        api_token = raw_api_token.split(':', 1)[1]
    else:
        # Use the full api_token or fall back to password
        api_token = raw_api_token or settings.get('password', '')
    
    if not api_token:
        raise ValueError("Confluence API token or password is required. Please configure in Settings.")
    
    # Create temporary file for Markdown
    temp_file = None
    temp_fd = None
    try:
        # Create temporary file
        temp_fd, temp_path = tempfile.mkstemp(suffix='.md', prefix='confluence_', text=True)
        temp_file = Path(temp_path)
        
        # Close the file descriptor immediately since we'll use the path, not the descriptor
        # mkstemp() opens the file, but we need to close it so other processes can write to it
        os.close(temp_fd)
        temp_fd = None  # Mark as closed to avoid closing again in finally
        
        logger.info(f"Exporting Confluence page {page_id} to Markdown...")
        
        # Check if confluence-markdown-exporter CLI is available
        # Try multiple possible command formats
        exporter_cmd = None
        possible_commands = [
            'confluence-markdown-exporter',
            'confluence_markdown_exporter',
            ['python', '-m', 'confluence_markdown_exporter'],
            ['python3', '-m', 'confluence_markdown_exporter'],
        ]
        
        for cmd_name in possible_commands:
            if isinstance(cmd_name, list):
                # Try Python module execution
                try:
                    result = subprocess.run(
                        cmd_name + ['--help'],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        check=False
                    )
                    stdout_lower = (result.stdout or '').lower()
                    stderr_lower = (result.stderr or '').lower()
                    if result.returncode == 0 or 'usage' in stdout_lower or 'usage' in stderr_lower:
                        exporter_cmd = cmd_name
                        break
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
            else:
                # Try direct command
                found_cmd = shutil.which(cmd_name)
                if found_cmd:
                    exporter_cmd = [found_cmd]
                    break
        
        if not exporter_cmd:
            raise ValueError("confluence-markdown-exporter CLI tool not found. Please ensure it is installed: pip install confluence-markdown-exporter==1.0.4")
        
        # Build command arguments for confluence-markdown-exporter CLI
        # Try different possible CLI argument formats
        cmd_variants = [
            # Format 1: --url --username --token page_id output
            exporter_cmd + [
                '--url', confluence_url,
                '--username', username,
                '--token', api_token,
                page_id,
                str(temp_file)
            ],
            # Format 2: --base-url --user --api-token page_id output
            exporter_cmd + [
                '--base-url', confluence_url,
                '--user', username,
                '--api-token', api_token,
                page_id,
                str(temp_file)
            ],
            # Format 3: url username token page_id output (positional)
            exporter_cmd + [
                confluence_url,
                username,
                api_token,
                page_id,
                str(temp_file)
            ],
        ]
        
        # Try each command format until one succeeds
        last_error = None
        for cmd in cmd_variants:
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout
                    check=True
                )
                logger.debug(f"confluence-markdown-exporter output: {result.stdout}")
                break  # Success, exit the loop
            except subprocess.TimeoutExpired as e:
                error_msg = f"Timeout while exporting Confluence page {page_id}. The operation took longer than 5 minutes."
                last_error = error_msg
                logger.debug(f"Command format timed out: {cmd}, error: {error_msg}")
                continue  # Try next format
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr or e.stdout or "Unknown error"
                last_error = error_msg
                logger.debug(f"Command format failed: {cmd}, error: {error_msg}")
                continue  # Try next format
        else:
            # All formats failed
            raise ValueError(f"Failed to export Confluence page {page_id} using confluence-markdown-exporter. Last error: {last_error}")
        
        if not temp_file.exists() or temp_file.stat().st_size == 0:
            raise ValueError(f"Failed to export Confluence page {page_id} to Markdown - output file is empty or missing")
        
        logger.info(f"Successfully exported page {page_id} to {temp_file}")
        
        # Embed the Markdown file
        embed_file(
            str(temp_file),
            collection_name=None,
            version=version,
            overwrite=overwrite
        )
        
        # Get filename for response (use page ID as base name)
        filename = f"confluence-page-{page_id}.md"
        
        return {
            "message": f"Confluence page {page_id} imported successfully",
            "filename": filename,
            "version": version,
            "mode": "overwrite" if overwrite else "incremental"
        }
        
    except Exception as e:
        logger.error(f"Error importing Confluence page {page_id}: {e}")
        raise
    finally:
        # Close file descriptor if still open
        if temp_fd is not None:
            try:
                os.close(temp_fd)
            except Exception as e:
                logger.warning(f"Failed to close temporary file descriptor: {e}")
        
        # Clean up temporary file
        if temp_file and temp_file.exists():
            try:
                temp_file.unlink()
                logger.info(f"Cleaned up temporary file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file {temp_file}: {e}")

