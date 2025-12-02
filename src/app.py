"""
Flask API Server
RESTful API for embedding and querying documentation.
"""
from flask import Flask, request, jsonify, session, Response, stream_with_context
from flask_cors import CORS
import os
import sys
from pathlib import Path
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import requests
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import signal
from .timeout_decorator import timeout, TimeoutError as CustomTimeoutError

# Handle imports for both module and standalone execution
if __name__ == '__main__':
    from embed import embed_file, embed_directory, embed_confluence_page, embed_confluence_pages, import_confluence_page_to_vector_db, embed_url
    from query import query_docs, query_simple
    from utils import setup_logging
    from settings import get_confluence_settings, save_confluence_settings, get_system_settings, save_system_settings, get_llm_providers, save_llm_providers, get_active_llm_provider, get_active_embedding_provider
    from llm_providers import LLMProviderFactory, EmbeddingProviderFactory
    from confluence import ConfluenceIntegration
    # Multi-version and history not available in standalone mode
    query_multiple_versions = None
    compare_versions = None
    get_query_history = None
    requires_auth = lambda f: f  # No-op decorator
    requires_write_auth = lambda f: f
else:
    from .embed import embed_file, embed_directory, embed_confluence_page, embed_confluence_pages, import_confluence_page_to_vector_db, embed_url
    from .query import query_docs, query_simple
    from .multi_version_query import query_multiple_versions, compare_versions
    from .query_history import get_query_history
    from .utils import setup_logging, redact_api_keys, redact_config, RedactingFormatter
    from .auth import requires_auth, requires_write_auth, get_auth_status
    from .code_extractor import extract_code_from_document, format_code_for_response
    from .settings import get_confluence_settings, save_confluence_settings, get_system_settings, save_system_settings, get_llm_providers, save_llm_providers, get_active_llm_provider, get_active_embedding_provider
    from .llm_providers import LLMProviderFactory, EmbeddingProviderFactory
    from .confluence import ConfluenceIntegration

load_dotenv()

app = Flask(__name__)
# Configure session
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_SECURE', 'false').lower() == 'true'

# Enable CORS with credentials support for session cookies
CORS(app, supports_credentials=True)

# Initialize logger early (needed for rate limiting configuration)
logger = setup_logging()

# Configure rate limiting
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    import redis
    
    # Try to use Redis for distributed rate limiting (if available)
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    redis_available = False
    
    # Test Redis connection first with a short timeout
    try:
        redis_client = redis.from_url(redis_url, socket_connect_timeout=0.5, socket_timeout=0.5)
        redis_client.ping()
        redis_available = True
        logger.info("Redis available for rate limiting")
    except Exception as e:
        logger.warning(f"Redis not available for rate limiting ({type(e).__name__}: {str(e)}), using in-memory storage")
        redis_available = False
    
    # Always use in-memory storage by default to avoid Redis connection issues
    # Redis can be enabled later via USE_REDIS_RATE_LIMITING=true when properly configured
    use_redis = os.getenv('USE_REDIS_RATE_LIMITING', 'false').lower() == 'true'
    
    if use_redis and redis_available:
        try:
            limiter = Limiter(
                app=app,
                key_func=get_remote_address,
                storage_uri=redis_url,
                default_limits=["200 per day", "50 per hour"],
                strategy="fixed-window",
                on_breach=lambda request, endpoint, limits: logger.warning(f"Rate limit breached for {endpoint}"),
                swallow_errors=True  # Don't fail requests if rate limiting fails
            )
            logger.info("Rate limiting using Redis storage")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis rate limiter ({e}), falling back to in-memory")
            use_redis = False
    
    if not use_redis or not redis_available:
        # Use in-memory storage (works without Redis)
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=["200 per day", "50 per hour"],
            strategy="fixed-window",
            swallow_errors=True  # Don't fail requests if rate limiting fails
        )
        logger.info("Rate limiting using in-memory storage (Redis not required)")
except ImportError:
    logger.warning("Flask-Limiter not installed, rate limiting disabled")
    limiter = None
except Exception as e:
    logger.error(f"Failed to initialize rate limiter: {e}", exc_info=True)
    limiter = None

# Ensure temp directory exists
TEMP_DIR = Path(os.getenv('TEMP_FOLDER', './_temp'))
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Configure werkzeug (Flask's HTTP request logger) to redact API keys
import logging
from .utils import RedactingFormatter

werkzeug_logger = logging.getLogger('werkzeug')
# Apply redacting formatter to all werkzeug handlers
for handler in werkzeug_logger.handlers:
    handler.setFormatter(RedactingFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    try:
        # Check if configured LLM provider is accessible
        try:
            provider_config = get_active_llm_provider()
            llm = LLMProviderFactory.get_llm(provider_config['type'], provider_config)
            llm_available = True
            llm_provider = provider_config['type']
        except Exception as e:
            llm_available = False
            llm_provider = 'unknown'
            logger.warning(f"LLM provider check failed: {e}")
        
        # Include auth status if available
        auth_status = {}
        try:
            if 'get_auth_status' in globals() and get_auth_status:
                auth_status = get_auth_status()
        except Exception:
            # Gracefully handle any errors when retrieving auth status
            # This allows the health check to continue even if auth status is unavailable
            pass
        
        response = {
            "status": "healthy" if llm_available else "degraded",
            "service": "RAG API",
            "llm_available": llm_available,
            "llm_provider": llm_provider
        }
        response.update(auth_status)
        
        status_code = 200 if llm_available else 503
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({
            "status": "degraded",
            "service": "RAG API",
            "llm_available": False,
            "error": str(e)
        }), 503


@app.route('/embed', methods=['POST'])
@requires_write_auth
@(limiter.limit("10 per minute") if limiter else lambda f: f)
def embed():
    """Embed a single file into the vector database."""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    version = request.form.get('version')  # Optional version parameter
    collection_name = request.form.get('collection_name')  # Optional collection name parameter
    overwrite = request.form.get('overwrite', 'false').lower() == 'true'
    
    # SECURITY: Sanitize filename to prevent path traversal attacks
    safe_filename = secure_filename(file.filename)
    if not safe_filename:
        return jsonify({"error": "Invalid filename"}), 400
    
    # Use absolute path to ensure we stay within TEMP_DIR
    file_path = TEMP_DIR / safe_filename
    
    # Additional security: Ensure resolved path is still within TEMP_DIR
    try:
        file_path = file_path.resolve()
        if not str(file_path).startswith(str(TEMP_DIR.resolve())):
            return jsonify({"error": "Invalid file path"}), 400
    except (OSError, ValueError):
        return jsonify({"error": "Invalid file path"}), 400
    
    # Save file
    try:
        file.save(str(file_path))
        logger.info(f"File saved: {file_path}")
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        return jsonify({"error": f"Failed to save file: {str(e)}"}), 500
    
    try:
        # Apply 60 second timeout to embedding operations
        embed_timeout = int(os.getenv('EMBED_TIMEOUT', 60))
        
        @timeout(embed_timeout)
        def execute_embed():
            return embed_file(str(file_path), collection_name=collection_name, version=version, overwrite=overwrite)
        
        try:
            execute_embed()
        except CustomTimeoutError as e:
            logger.warning(f"Embedding timeout after {embed_timeout}s: {safe_filename}")
            return jsonify({
                "error": f"Embedding timed out after {embed_timeout} seconds. The file may be too large.",
                "timeout": embed_timeout
            }), 504
        
        return jsonify({
            "message": "File embedded successfully",
            "version": version,
            "collection_name": collection_name,
            "mode": "overwrite" if overwrite else "incremental",
            "filename": safe_filename
        }), 200
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return jsonify({"error": f"Embedding failed: {str(e)}"}), 500
    finally:
        # Clean up temporary file
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary file: {e}")


@app.route('/embed-batch', methods=['POST'])
@requires_write_auth
def embed_batch():
    """Embed multiple files from a directory."""
    if 'directory' not in request.form:
        return jsonify({"error": "No directory provided"}), 400
    
    directory_path = request.form.get('directory')
    version = request.form.get('version')
    collection_name = request.form.get('collection_name')  # Optional collection name parameter
    overwrite = request.form.get('overwrite', 'false').lower() == 'true'
    
    # SECURITY: Validate directory path
    try:
        directory_path = Path(directory_path).resolve()
        # Add additional security checks here if needed
        if not directory_path.is_dir():
            return jsonify({"error": "Invalid directory path"}), 400
    except (OSError, ValueError) as e:
        return jsonify({"error": f"Invalid directory path: {str(e)}"}), 400
    
    try:
        results = embed_directory(
            str(directory_path),
            collection_name=collection_name,
            version=version,
            overwrite=overwrite
        )
        return jsonify({
            "message": "Batch embedding completed",
            "results": results,
            "version": version,
            "collection_name": collection_name
        }), 200
    except Exception as e:
        logger.error(f"Batch embedding failed: {e}")
        return jsonify({"error": f"Batch embedding failed: {str(e)}"}), 500


@app.route('/embed-url', methods=['POST'])
@requires_write_auth
@(limiter.limit("10 per minute") if limiter else lambda f: f)
def embed_url_endpoint():
    """Start background job to embed content from a URL."""
    data = request.get_json() or request.form
    
    url = data.get('url')
    version = data.get('version')
    collection_name = data.get('collection_name')
    overwrite = str(data.get('overwrite', 'false')).lower() == 'true'
    max_depth = int(data.get('max_depth', 3))
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    # Try to use Celery for async execution
    try:
        from .tasks import scrape_and_embed_url_task
        
        # Start background task
        task = scrape_and_embed_url_task.delay(
            url=url,
            collection_name=collection_name,
            version=version,
            overwrite=overwrite,
            max_depth=max_depth
        )
        
        return jsonify({
            "message": "URL scraping and embedding job started",
            "task_id": task.id,
            "status_url": f"/embed-url/status/{task.id}"
        }), 202  # 202 Accepted for async operations
        
    except ImportError:
        # Fallback to synchronous execution if Celery is not available
        logger.warning("Celery not available, using synchronous execution")
        try:
            results = embed_url(
                url,
                collection_name=collection_name,
                version=version,
                overwrite=overwrite,
                max_depth=max_depth
            )
            
            return jsonify({
                "message": "URL scraping and embedding completed",
                "results": results,
                "version": version,
                "collection_name": collection_name
            }), 200
            
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error(f"URL embedding failed: {e}")
            return jsonify({"error": f"URL embedding failed: {str(e)}"}), 500
    
    except Exception as e:
        logger.error(f"Failed to start URL embedding task: {e}")
        return jsonify({"error": f"Failed to start task: {str(e)}"}), 500


@app.route('/embed-url/status/<task_id>', methods=['GET'])
@requires_write_auth  # Use write_auth which allows GET without auth if AUTH_REQUIRED_FOR is 'write'
@(limiter.exempt if limiter else lambda f: f)
def embed_url_status(task_id):
    """Get status of a URL embedding task (single request)."""
    try:
        from .tasks import scrape_and_embed_url_task
        from celery.result import AsyncResult
        
        task_result = AsyncResult(task_id, app=scrape_and_embed_url_task.app)
        
        if task_result.state == 'PENDING':
            response = {
                'state': task_result.state,
                'status': 'Task is waiting to be processed'
            }
        elif task_result.state == 'PROGRESS':
            info = task_result.info or {}
            response = {
                'state': task_result.state,
                'status': info.get('status', 'Processing'),
                'progress': info.get('progress', 0),
                'url': info.get('url', '')
            }
        elif task_result.state == 'SUCCESS':
            response = {
                'state': task_result.state,
                'status': 'completed',
                'result': task_result.result
            }
        elif task_result.state == 'REVOKED':
            response = {
                'state': task_result.state,
                'status': 'cancelled',
                'error': 'Task was cancelled'
            }
        else:  # FAILURE
            response = {
                'state': task_result.state,
                'status': 'failed',
                'error': str(task_result.info) if task_result.info else 'Unknown error'
            }
        
        return jsonify(response), 200
        
    except ImportError:
        return jsonify({"error": "Celery is not configured"}), 503
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        return jsonify({"error": f"Failed to get task status: {str(e)}"}), 500


@app.route('/embed-url/cancel/<task_id>', methods=['POST'])
@requires_write_auth
@(limiter.exempt if limiter else lambda f: f)
def cancel_embed_url_task(task_id):
    """Cancel a running URL embedding task."""
    try:
        from .tasks import scrape_and_embed_url_task
        from celery.result import AsyncResult
        
        task_result = AsyncResult(task_id, app=scrape_and_embed_url_task.app)
        
        # Revoke the task
        task_result.revoke(terminate=True)
        
        logger.info(f"Task {task_id} revoked (cancelled)")
        
        return jsonify({
            "message": "Task cancellation requested",
            "task_id": task_id
        }), 200
        
    except ImportError:
        return jsonify({"error": "Celery is not configured"}), 503
    except Exception as e:
        logger.error(f"Failed to cancel task: {e}")
        return jsonify({"error": f"Failed to cancel task: {str(e)}"}), 500


@app.route('/embed-url/stream/<task_id>', methods=['GET'])
@(limiter.exempt if limiter else lambda f: f)
def embed_url_status_stream(task_id):
    """Stream real-time updates for a URL embedding task using Server-Sent Events."""
    import time
    import json
    
    # Check authentication manually (EventSource doesn't send cookies reliably)
    # Use same logic as requires_write_auth - allow if AUTH_REQUIRED_FOR is 'write' (GET requests don't need auth)
    from .auth import is_authenticated, AUTH_ENABLED, AUTH_REQUIRED_FOR
    
    # If auth is enabled and required for all operations, check authentication
    if AUTH_ENABLED and AUTH_REQUIRED_FOR == 'all':
        if not is_authenticated():
            # Send error as SSE event and close
            def error_stream():
                yield f"data: {json.dumps({'state': 'ERROR', 'error': 'Authentication required. Please log in.'})}\n\n"
            return Response(
                stream_with_context(error_stream()),
                mimetype='text/event-stream',
                status=200,  # Use 200 so EventSource can read the error message
                headers={
                    'Cache-Control': 'no-cache',
                    'X-Accel-Buffering': 'no',
                    'Connection': 'keep-alive'
                }
            )
    # If AUTH_REQUIRED_FOR is 'write', GET requests (like SSE) don't need auth
    
    try:
        from .tasks import scrape_and_embed_url_task
        from celery.result import AsyncResult
        
        def generate():
            """Generator function that yields SSE events."""
            task_result = AsyncResult(task_id, app=scrape_and_embed_url_task.app)
            last_state = None
            last_progress = -1
            last_status = None
            poll_interval = 0.5  # Poll every 0.5 seconds for more responsive updates
            
            try:
                while True:
                    # Check if client disconnected (no timeout - stream stays open as long as task runs)
                    try:
                        task_result = AsyncResult(task_id, app=scrape_and_embed_url_task.app)
                        current_state = task_result.state
                        
                        # Build response based on state
                        if current_state == 'PENDING':
                            response = {
                                'state': 'PENDING',
                                'status': 'Task is waiting to be processed',
                                'progress': 0
                            }
                        elif current_state == 'STARTED':
                            # Task has started but hasn't updated state yet
                            response = {
                                'state': 'PROGRESS',
                                'status': 'Task starting...',
                                'progress': 0
                            }
                        elif current_state == 'PROGRESS':
                            info = task_result.info or {}
                            progress = info.get('progress', 0)
                            response = {
                                'state': current_state,
                                'status': info.get('status', 'Processing'),
                                'progress': progress,
                                'url': info.get('url', '')
                            }
                        elif current_state == 'SUCCESS':
                            response = {
                                'state': current_state,
                                'status': 'completed',
                                'progress': 100,
                                'result': task_result.result
                            }
                            # Send final event and close
                            yield f"data: {json.dumps(response)}\n\n"
                            break
                        elif current_state == 'REVOKED':
                            response = {
                                'state': current_state,
                                'status': 'cancelled',
                                'error': 'Task was cancelled'
                            }
                            # Send cancellation event and close
                            yield f"data: {json.dumps(response)}\n\n"
                            break
                        elif current_state == 'FAILURE':
                            response = {
                                'state': current_state,
                                'status': 'failed',
                                'error': str(task_result.info) if task_result.info else 'Unknown error'
                            }
                            # Send error event and close
                            yield f"data: {json.dumps(response)}\n\n"
                            break
                        elif current_state == 'RETRY':
                            # Task is being retried
                            response = {
                                'state': 'PROGRESS',
                                'status': 'Task is being retried...',
                                'progress': 0
                            }
                        else:
                            # Unknown state - treat as in progress
                            logger.warning(f"Unknown task state: {current_state} for task {task_id}")
                            response = {
                                'state': 'PROGRESS',
                                'status': f'Task state: {current_state}',
                                'progress': 0
                            }
                        
                        # Always send updates for PROGRESS state to show real-time progress
                        # Also send if status message changed (even if progress is same)
                        current_progress = response.get('progress', 0)
                        current_status = response.get('status', '')
                        should_send = (
                            current_state == 'PROGRESS' or 
                            current_state != last_state or 
                            current_progress != last_progress or
                            current_status != last_status
                        )
                        
                        if should_send:
                            yield f"data: {json.dumps(response)}\n\n"
                            last_state = current_state
                            last_progress = current_progress
                            last_status = current_status
                        
                        # If task is complete, break
                        if current_state in ('SUCCESS', 'FAILURE'):
                            break
                            
                    except Exception as e:
                        logger.error(f"Error checking task status: {e}")
                        yield f"data: {json.dumps({'state': 'ERROR', 'error': str(e)})}\n\n"
                        break
                    
                    # Wait before next poll
                    time.sleep(poll_interval)
                    
            except GeneratorExit:
                # Client disconnected
                logger.info(f"SSE stream closed for task {task_id}")
            except Exception as e:
                logger.error(f"Error in SSE stream for task {task_id}: {e}")
                yield f"data: {json.dumps({'state': 'ERROR', 'error': str(e)})}\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',  # Disable buffering in nginx
                'Connection': 'keep-alive'
            }
        )
        
    except ImportError:
        return jsonify({"error": "Celery is not configured"}), 503
    except Exception as e:
        logger.error(f"Failed to create SSE stream: {e}")
        return jsonify({"error": f"Failed to create stream: {str(e)}"}), 500


@app.route('/query', methods=['POST'])
@(limiter.limit("30 per minute") if limiter else lambda f: f)
def query():
    """Query the documentation using natural language."""
    import time
    
    # Start overall request timing
    request_start_time = time.time()
    
    # SECURITY: Check if request has JSON body
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    data = request.json
    if data is None:
        return jsonify({"error": "Invalid or missing JSON body"}), 400
    
    question = data.get('query')
    if not question:
        return jsonify({"error": "Missing 'query' field in request body"}), 400
    
    # Optional parameters
    collection_name = data.get('collection_name')
    version = data.get('version')
    k = data.get('k', 3)  # Number of documents to retrieve
    use_simple = data.get('simple', False)  # Use simple query (faster)
    
    try:
        # Apply 30 second timeout to query operations
        query_timeout = int(os.getenv('QUERY_TIMEOUT', 30))
        
        @timeout(query_timeout)
        def execute_query():
            if use_simple:
                return query_simple(question, collection_name, version, k)
            else:
                return query_docs(question, collection_name, version, k)
        
        try:
            result = execute_query()
        except CustomTimeoutError as e:
            logger.warning(f"Query timeout after {query_timeout}s: {question[:100]}")
            return jsonify({
                "error": f"Query timed out after {query_timeout} seconds. Please try a simpler query or reduce the number of documents (k).",
                "timeout": query_timeout
            }), 504
        
        # Format response - convert Document objects to dicts for JSON serialization
        sources = []
        for doc in result.get('source_documents', []):
            if hasattr(doc, 'page_content'):
                sources.append({
                    "content": doc.page_content[:500] if doc.page_content else "",  # First 500 chars
                    "metadata": doc.metadata if hasattr(doc, 'metadata') else {}
                })
            elif isinstance(doc, dict):
                sources.append({
                    "content": doc.get('page_content', doc.get('content', ''))[:500],
                    "metadata": doc.get('metadata', {})
                })
            else:
                # Fallback: convert to string representation
                sources.append({
                    "content": str(doc)[:500],
                    "metadata": {}
                })
        
        # Get statistics from result
        stats = result.get('stats', {})
        request_total_time = time.time() - request_start_time
        
        # Add request overhead time (time not accounted for in query processing)
        stats['request_overhead_time'] = max(0, request_total_time - stats.get('total_time', 0))
        stats['request_total_time'] = request_total_time
        
        response = {
            "answer": result.get('result', ''),
            "query": result.get('query', question),
            "sources": sources,
            "source_count": len(sources),
            "stats": stats
        }
        
        # Log statistics
        logger.info(f"Query statistics for '{question[:50]}...': "
                   f"Total: {stats.get('request_total_time', 0):.3f}s | "
                   f"Cache lookup: {stats.get('cache_lookup_time', 0):.3f}s | "
                   f"LLM init: {stats.get('llm_init_time', 0):.3f}s | "
                   f"Vector DB init: {stats.get('vector_db_init_time', 0):.3f}s | "
                   f"Multi-query gen: {stats.get('multi_query_generation_time', 0):.3f}s | "
                   f"Doc retrieval: {stats.get('document_retrieval_time', 0):.3f}s | "
                   f"Answer gen: {stats.get('answer_generation_time', 0):.3f}s | "
                   f"Cache store: {stats.get('cache_store_time', 0):.3f}s | "
                   f"Overhead: {stats.get('request_overhead_time', 0):.3f}s")
        
        # Add to query history
        try:
            history = get_query_history()
            history.add_query(
                question,
                answer=result['result'],
                version=version,
                response_time=stats.get('request_total_time'),
                source_count=len(result['source_documents'])
            )
        except Exception as e:
            logger.warning(f"Failed to add query to history: {e}")
        
        return jsonify(response), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Query failed: {e}")
        return jsonify({"error": f"Query failed: {str(e)}"}), 500


@app.route('/collections', methods=['GET'])
@(limiter.exempt if limiter else lambda f: f)
def list_collections():
    """List all available collections."""
    try:
        import chromadb
        client = chromadb.PersistentClient(path=os.getenv('CHROMA_PATH', 'chroma'))
        collections = client.list_collections()
        
        collection_info = []
        for collection in collections:
            try:
                # Try to get count, handle errors gracefully
                count = collection.count()
            except Exception as count_error:
                logger.warning(f"Could not get count for collection {collection.name}: {count_error}")
                count = 0  # Use 0 if count cannot be determined
            
            collection_info.append({
                "name": collection.name,
                "count": count
            })
        
        return jsonify({
            "collections": collection_info,
            "total": len(collection_info)
        }), 200
    except Exception as e:
        logger.error(f"Error listing collections: {e}", exc_info=True)
        return jsonify({"error": f"Failed to list collections: {str(e)}"}), 500


@app.route('/collections/<version>', methods=['GET'])
def get_collection_info(version):
    """Get information about a specific collection."""
    try:
        import chromadb
        from .utils import generate_collection_name
        import re
        
        client = chromadb.PersistentClient(path=os.getenv('CHROMA_PATH', 'chroma'))
        base_name = os.getenv('COLLECTION_NAME', 'common-model-docs')
        
        # Try to determine if version is actually a version number or a full collection name
        collection_name = None
        collection = None
        
        # Check if version looks like a version number (contains digits)
        if re.match(r'^[\d.]+$', version):
            # It's a version number, use versioned collection name
            collection_name = generate_collection_name(base_name, version)
        else:
            # It might be a full collection name, try as-is first
            try:
                collection = client.get_collection(name=version)
                collection_name = version
            except Exception:
                # If that fails, try with version suffix
                collection_name = generate_collection_name(base_name, version)
        
        if not collection:
            collection = client.get_collection(name=collection_name)
        
        return jsonify({
            "name": collection.name,
            "count": collection.count(),
            "version": version
        }), 200
    except Exception as e:
        logger.error(f"Error getting collection info: {e}")
        return jsonify({"error": f"Collection not found or error: {str(e)}"}), 404


@app.route('/collections/<version>', methods=['DELETE'])
@requires_write_auth
def delete_collection(version):
    """Delete a specific collection."""
    try:
        import chromadb
        from .utils import generate_collection_name
        import re
        
        client = chromadb.PersistentClient(path=os.getenv('CHROMA_PATH', 'chroma'))
        base_name = os.getenv('COLLECTION_NAME', 'common-model-docs')
        
        # Try to determine if version is actually a version number or a full collection name
        collection_name = None
        
        # Always try as collection name first (most common case from UI)
        try:
            # Try to get the collection to verify it exists
            client.get_collection(name=version)
            collection_name = version
        except Exception:
            # Not a direct collection name, try to construct it
            if re.match(r'^[\d.]+$', version):
                # It's a version number, use versioned collection name
                collection_name = generate_collection_name(base_name, version)
            else:
                # Try with version suffix as fallback
                collection_name = generate_collection_name(base_name, version)
        
        # Delete the collection
        client.delete_collection(name=collection_name)
        
        logger.info(f"Collection {collection_name} deleted successfully")
        return jsonify({
            "message": f"Collection {collection_name} deleted successfully",
            "version": version
        }), 200
    except Exception as e:
        logger.error(f"Error deleting collection: {e}")
        return jsonify({"error": f"Failed to delete collection: {str(e)}"}), 500


@app.route('/collections/<version>/documents', methods=['GET'])
@requires_auth
def list_collection_documents(version):
    """List all documents in a specific collection."""
    try:
        import chromadb
        from .utils import generate_collection_name
        
        client = chromadb.PersistentClient(path=os.getenv('CHROMA_PATH', 'chroma'))
        base_name = os.getenv('COLLECTION_NAME', 'common-model-docs')
        
        # Try to determine if version is actually a version number or a full collection name
        # First, try the version as-is (in case it's a full collection name)
        # Then try with version suffix (in case it's a version number)
        collection_name = None
        collection = None
        
        # Always try as collection name first (most common case from UI)
        try:
            collection = client.get_collection(name=version)
            collection_name = version
        except Exception:
            # Not a direct collection name, try to construct it
            import re
            if re.match(r'^[\d.]+$', version):
                # It's a version number, use versioned collection name
                collection_name = generate_collection_name(base_name, version)
            else:
                # Try with version suffix as fallback
                collection_name = generate_collection_name(base_name, version)
            
            # Try to get the collection with the constructed name
            try:
                collection = client.get_collection(name=collection_name)
            except Exception as e:
                logger.error(f"Collection not found: {collection_name} (from version param: {version})")
                raise
        
        # Get all documents from the collection
        # Using limit=None to get all documents, but we'll use a reasonable limit
        # ChromaDB's get() method can retrieve all documents
        results = collection.get(limit=None)
        
        documents = []
        if results and results.get('ids'):
            # Use 'or []' to handle both missing key and None value cases
            metadatas = results.get('metadatas') or []
            for i, doc_id in enumerate(results['ids']):
                # Safely get metadata with bounds checking
                metadata = metadatas[i] if i < len(metadatas) else {}
                documents.append({
                    'id': doc_id,
                    'metadata': metadata,
                    'source': metadata.get('source_file', metadata.get('source', 'Unknown')),
                    'page': metadata.get('page', ''),
                    'chunk_index': metadata.get('chunk_index', '')
                })
        
        return jsonify({
            "version": version,
            "collection_name": collection_name,
            "documents": documents,
            "total": len(documents)
        }), 200
    except Exception as e:
        logger.error(f"Error listing collection documents: {e}")
        return jsonify({"error": f"Failed to list documents: {str(e)}"}), 500


@app.route('/collections/<version>/documents/<doc_id>', methods=['DELETE'])
@requires_write_auth
def delete_collection_document(version, doc_id):
    """Delete a specific document from a collection."""
    try:
        import chromadb
        from .utils import generate_collection_name
        import re
        
        client = chromadb.PersistentClient(path=os.getenv('CHROMA_PATH', 'chroma'))
        base_name = os.getenv('COLLECTION_NAME', 'common-model-docs')
        
        # Try to determine if version is actually a version number or a full collection name
        collection_name = None
        collection = None
        
        # Check if version looks like a version number (contains digits)
        if re.match(r'^[\d.]+$', version):
            # It's a version number, use versioned collection name
            collection_name = generate_collection_name(base_name, version)
        else:
            # It might be a full collection name, try as-is first
            try:
                collection = client.get_collection(name=version)
                collection_name = version
            except Exception:
                # If that fails, try with version suffix
                collection_name = generate_collection_name(base_name, version)
        
        if not collection:
            collection = client.get_collection(name=collection_name)
        
        # Delete the document by ID
        collection.delete(ids=[doc_id])
        
        logger.info(f"Document {doc_id} deleted from collection {collection_name}")
        return jsonify({
            "message": f"Document deleted successfully",
            "version": version,
            "document_id": doc_id
        }), 200
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        return jsonify({"error": f"Failed to delete document: {str(e)}"}), 500


@app.route('/stats', methods=['GET'])
def get_stats():
    """Get system statistics including query and embedding metrics."""
    try:
        from .monitoring import get_query_monitor, get_embedding_monitor
        from .cache import get_cache
        
        days = int(request.args.get('days', 7))
        
        query_monitor = get_query_monitor()
        embedding_monitor = get_embedding_monitor()
        cache = get_cache()
        
        stats = {
            'query_stats': query_monitor.get_query_stats(days),
            'embedding_stats': embedding_monitor.get_embedding_stats(days),
            'cache_stats': cache.stats()
        }
        
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({"error": f"Failed to get stats: {str(e)}"}), 500


@app.route('/cache/clear', methods=['POST'])
@requires_auth
def clear_cache():
    """Clear the query cache."""
    try:
        from .cache import get_cache
        cache = get_cache()
        cache.clear()
        return jsonify({"message": "Cache cleared successfully"}), 200
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return jsonify({"error": f"Failed to clear cache: {str(e)}"}), 500


@app.route('/query/multi-version', methods=['POST'])
def query_multi_version():
    """Query documentation across multiple versions."""
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    data = request.json
    if data is None:
        return jsonify({"error": "Invalid or missing JSON body"}), 400
    
    question = data.get('query')
    versions = data.get('versions', [])
    
    if not question:
        return jsonify({"error": "Missing 'query' field"}), 400
    
    if not versions or not isinstance(versions, list):
        return jsonify({"error": "Missing or invalid 'versions' field (must be a list)"}), 400
    
    try:
        result = query_multiple_versions(
            question,
            versions=versions,
            k=data.get('k', 3)
        )
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Multi-version query failed: {e}")
        return jsonify({"error": f"Query failed: {str(e)}"}), 500


@app.route('/query/compare', methods=['POST'])
def query_compare():
    """Compare answers across different versions."""
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    data = request.json
    if data is None:
        return jsonify({"error": "Invalid or missing JSON body"}), 400
    
    question = data.get('query')
    versions = data.get('versions', [])
    
    if not question:
        return jsonify({"error": "Missing 'query' field"}), 400
    
    if not versions or not isinstance(versions, list) or len(versions) < 2:
        return jsonify({"error": "At least 2 versions required for comparison"}), 400
    
    try:
        result = compare_versions(
            question,
            versions=versions,
            k=data.get('k', 3)
        )
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Version comparison failed: {e}")
        return jsonify({"error": f"Comparison failed: {str(e)}"}), 500


@app.route('/history', methods=['GET'])
def get_history():
    """Get query history."""
    try:
        history = get_query_history()
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        entries = history.get_history(limit=limit, offset=offset)
        return jsonify({
            "history": entries,
            "total": len(history._load_history()),
            "limit": limit,
            "offset": offset
        }), 200
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        return jsonify({"error": f"Failed to get history: {str(e)}"}), 500


@app.route('/history/search', methods=['GET'])
def search_history():
    """Search query history."""
    try:
        history = get_query_history()
        search_term = request.args.get('q', '')
        limit = int(request.args.get('limit', 20))
        
        if not search_term:
            return jsonify({"error": "Missing 'q' parameter"}), 400
        
        results = history.search_history(search_term, limit=limit)
        return jsonify({
            "results": results,
            "count": len(results)
        }), 200
    except Exception as e:
        logger.error(f"Error searching history: {e}")
        return jsonify({"error": f"Failed to search history: {str(e)}"}), 500


@app.route('/history/export', methods=['GET'])
def export_history():
    """Export query history."""
    try:
        history = get_query_history()
        format = request.args.get('format', 'json')
        
        exported = history.export_history(format=format)
        
        if format == 'json':
            import json as json_module
            return jsonify(json_module.loads(exported)), 200
        else:
            from flask import Response
            return Response(
                exported,
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment; filename=query_history.csv'}
            )
    except Exception as e:
        logger.error(f"Error exporting history: {e}")
        return jsonify({"error": f"Failed to export history: {str(e)}"}), 500


@app.route('/favorites', methods=['GET', 'POST', 'DELETE'])
@requires_write_auth
def manage_favorites():
    """Manage favorite queries."""
    try:
        history = get_query_history()
        
        if request.method == 'GET':
            favorites = history.get_favorites()
            return jsonify({"favorites": favorites}), 200
        
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        data = request.json
        query = data.get('query')
        
        if not query:
            return jsonify({"error": "Missing 'query' field"}), 400
        
        if request.method == 'POST':
            history.add_favorite(query)
            return jsonify({"message": "Added to favorites"}), 200
        elif request.method == 'DELETE':
            history.remove_favorite(query)
            return jsonify({"message": "Removed from favorites"}), 200
    
    except Exception as e:
        logger.error(f"Error managing favorites: {e}")
        return jsonify({"error": f"Failed to manage favorites: {str(e)}"}), 500


@app.route('/extract-code', methods=['POST'])
@requires_write_auth
def extract_code():
    """Extract code examples from text or document."""
    if extract_code_from_document is None:
        return jsonify({"error": "Code extraction module not available"}), 501
    
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    data = request.json
    if data is None:
        return jsonify({"error": "Invalid or missing JSON body"}), 400
    
    text = data.get('text')
    language = data.get('language')  # Optional: filter by language
    
    if not text:
        return jsonify({"error": "Missing 'text' field in request body"}), 400
    
    try:
        result = extract_code_from_document(text, language=language)
        
        # Format code blocks for response
        formatted_blocks = [
            format_code_for_response(block)
            for block in result['blocks']
        ]
        
        return jsonify({
            "total_blocks": result['total_blocks'],
            "languages": result['languages'],
            "blocks": formatted_blocks
        }), 200
    except Exception as e:
        logger.error(f"Code extraction failed: {e}")
        return jsonify({"error": f"Code extraction failed: {str(e)}"}), 500


@app.route('/auth/login', methods=['POST'])
def login():
    """Login endpoint for username/password authentication."""
    try:
        from .auth import verify_credentials, VALID_USERNAME
        
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({
                "error": "Missing credentials",
                "message": "Username and password are required"
            }), 400
        
        if verify_credentials(username, password):
            session['authenticated'] = True
            session['username'] = username
            logger.info(f"User {username} logged in successfully")
            return jsonify({
                "success": True,
                "message": "Login successful",
                "username": username
            }), 200
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            return jsonify({
                "error": "Invalid credentials",
                "message": "Username or password is incorrect"
            }), 401
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"error": f"Login failed: {str(e)}"}), 500


@app.route('/auth/logout', methods=['POST'])
def logout():
    """Logout endpoint."""
    try:
        username = session.get('username', 'unknown')
        session.clear()
        logger.info(f"User {username} logged out")
        return jsonify({
            "success": True,
            "message": "Logout successful"
        }), 200
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({"error": f"Logout failed: {str(e)}"}), 500


@app.route('/auth/status', methods=['GET'])
def auth_status():
    """Get authentication configuration status."""
    try:
        if 'get_auth_status' in globals() and get_auth_status:
            status = get_auth_status()
            return jsonify(status), 200
        else:
            return jsonify({
                "enabled": False,
                "message": "Authentication module not available"
            }), 200
    except (NameError, AttributeError, Exception) as e:
        return jsonify({"error": f"Failed to get auth status: {str(e)}"}), 500


@app.route('/settings/confluence', methods=['GET'])
@requires_auth
def get_confluence_settings_endpoint():
    """Get current Confluence settings."""
    try:
        settings = get_confluence_settings()
        # Don't return sensitive data in full
        safe_settings = {**settings}
        # Optionally mask password/token in response (or return empty)
        if 'password' in safe_settings:
            safe_settings['password'] = '***' if safe_settings['password'] else ''
        if 'api_token' in safe_settings:
            safe_settings['api_token'] = '***' if safe_settings['api_token'] else ''
        return jsonify(safe_settings), 200
    except Exception as e:
        logger.error(f"Failed to get Confluence settings: {e}")
        return jsonify({"error": f"Failed to get settings: {str(e)}"}), 500


@app.route('/settings/confluence', methods=['POST'])
@requires_write_auth
def save_confluence_settings_endpoint():
    """Save Confluence settings."""
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    data = request.json
    if data is None:
        return jsonify({"error": "Invalid or missing JSON body"}), 400
    
    try:
        # Validate required fields
        if 'url' not in data or not data['url']:
            return jsonify({"error": "URL is required"}), 400
        
        if 'instance_type' not in data or data['instance_type'] not in ['cloud', 'server']:
            return jsonify({"error": "instance_type must be 'cloud' or 'server'"}), 400
        
        # For cloud, require api_token or username+password
        if data['instance_type'] == 'cloud':
            if not data.get('api_token') and not (data.get('username') and data.get('password')):
                return jsonify({"error": "Cloud instance requires api_token or username+password"}), 400
        
        # For server, require api_token or username+password
        if data['instance_type'] == 'server':
            if not data.get('api_token') and not (data.get('username') and data.get('password')):
                return jsonify({"error": "Server instance requires api_token or username+password"}), 400
        
        # Save settings
        success = save_confluence_settings(data)
        if success:
            return jsonify({"message": "Settings saved successfully"}), 200
        else:
            return jsonify({"error": "Failed to save settings"}), 500
    except Exception as e:
        logger.error(f"Failed to save Confluence settings: {e}")
        return jsonify({"error": f"Failed to save settings: {str(e)}"}), 500


@app.route('/settings/system', methods=['GET'])
@requires_auth
def get_system_settings_endpoint():
    """Get current system settings."""
    try:
        settings = get_system_settings()
        # Convert snake_case to camelCase for frontend
        return jsonify({"systemName": settings.get("system_name", "RAGU")}), 200
    except Exception as e:
        logger.error(f"Failed to get system settings: {e}")
        return jsonify({"error": f"Failed to get settings: {str(e)}"}), 500


@app.route('/settings/system', methods=['POST'])
@requires_write_auth
def save_system_settings_endpoint():
    """Save system settings."""
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    data = request.json
    if data is None:
        return jsonify({"error": "Invalid or missing JSON body"}), 400
    
    try:
        # Validate required fields
        if 'system_name' not in data or not data['system_name'] or not data['system_name'].strip():
            return jsonify({"error": "System name is required and cannot be empty"}), 400
        
        # Save settings
        success = save_system_settings(data)
        if success:
            return jsonify({"message": "Settings saved successfully"}), 200
        else:
            return jsonify({"error": "Failed to save settings"}), 500
    except Exception as e:
        logger.error(f"Failed to save system settings: {e}")
        return jsonify({"error": f"Failed to save settings: {str(e)}"}), 500


@app.route('/settings/llm-providers', methods=['GET'])
@requires_auth
def get_llm_providers_endpoint():
    """Get all LLM provider configurations."""
    try:
        providers = get_llm_providers()
        return jsonify(providers), 200
    except Exception as e:
        logger.error(f"Failed to get LLM provider settings: {e}")
        return jsonify({"error": f"Failed to get settings: {str(e)}"}), 500


@app.route('/settings/llm-providers', methods=['POST'])
@requires_write_auth
def save_llm_providers_endpoint():
    """Save LLM provider configurations."""
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    data = request.json
    if data is None:
        return jsonify({"error": "Invalid or missing JSON body"}), 400
    
    try:
        # Validate structure
        if 'llm_providers' not in data:
            return jsonify({"error": "llm_providers is required"}), 400
        if 'embedding_providers' not in data:
            return jsonify({"error": "embedding_providers is required"}), 400
        
        # Save settings
        success = save_llm_providers(data)
        if success:
            return jsonify({"message": "LLM provider settings saved successfully"}), 200
        else:
            return jsonify({"error": "Failed to save settings"}), 500
    except Exception as e:
        logger.error(f"Failed to save LLM provider settings: {e}")
        return jsonify({"error": f"Failed to save settings: {str(e)}"}), 500


@app.route('/settings/llm-providers/active', methods=['GET'])
@requires_auth
def get_active_llm_providers_endpoint():
    """Get active LLM and embedding provider configurations."""
    try:
        active_llm = get_active_llm_provider()
        active_embedding = get_active_embedding_provider()
        return jsonify({
            "llm": active_llm,
            "embedding": active_embedding
        }), 200
    except Exception as e:
        logger.error(f"Failed to get active LLM providers: {e}")
        return jsonify({"error": f"Failed to get active providers: {str(e)}"}), 500


@app.route('/settings/llm-providers/models', methods=['GET'])
@requires_auth
def get_llm_provider_models():
    """Get available models for a provider, filtered by category (llm or embedding) and free only."""
    try:
        provider_type = request.args.get('provider_type')
        category = request.args.get('category', 'llm')  # 'llm' or 'embedding'
        api_key = request.args.get('api_key')  # Optional, for OpenRouter
        
        if not provider_type:
            return jsonify({"error": "provider_type is required"}), 400
        
        if category not in ['llm', 'embedding']:
            return jsonify({"error": "category must be 'llm' or 'embedding'"}), 400
        
        # For OpenRouter, fetch from their API
        if provider_type == 'openrouter':
            if not api_key:
                return jsonify({"error": "API key is required for OpenRouter"}), 400
            
            try:
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
                response = requests.get('https://openrouter.ai/api/v1/models', headers=headers, timeout=10)
                
                if response.status_code != 200:
                    return jsonify({
                        "error": f"Failed to fetch models from OpenRouter: {response.status_code}",
                        "models": []
                    }), 503
                
                models_data = response.json()
                all_models = models_data.get('data', [])
                
                # Filter models based on category and free pricing
                filtered_models = []
                for model in all_models:
                    model_id = model.get('id', '')
                    model_name = model.get('name', model_id)
                    pricing = model.get('pricing', {})
                    
                    # Check if model is free (prompt and completion prices are 0 or null)
                    prompt_price = pricing.get('prompt', '0')
                    completion_price = pricing.get('completion', '0')
                    is_free = (
                        (prompt_price == '0' or prompt_price == 0 or prompt_price is None) and
                        (completion_price == '0' or completion_price == 0 or completion_price is None)
                    )
                    
                    if not is_free:
                        continue  # Skip paid models
                    
                    # Check if model supports the requested category
                    modalities = model.get('modalities', [])
                    capabilities = model.get('capabilities', {})
                    
                    if category == 'embedding':
                        # Check for embedding support - be strict to avoid LLM models
                        # Only include models that explicitly support embeddings
                        supports_embeddings = (
                            'embeddings' in modalities or
                            'embedding' in modalities or
                            capabilities.get('embeddings', False)
                        ) or (
                            # Only allow models with 'embedding' in name if they're known embedding models
                            ('text-embedding' in model_id.lower() or 
                             model_id.lower().endswith('-embed') or
                             model_id.lower().startswith('embed-'))
                        )
                        if supports_embeddings:
                            # Try to get embedding dimension from model info
                            # Some models have this in their description or capabilities
                            embedding_dimension = None
                            if 'dimension' in model:
                                embedding_dimension = model.get('dimension')
                            elif 'embedding_dimension' in model:
                                embedding_dimension = model.get('embedding_dimension')
                            elif 'dimensions' in model:
                                embedding_dimension = model.get('dimensions')
                            
                            filtered_models.append({
                                'id': model_id,
                                'name': model_name,
                                'description': model.get('description', ''),
                                'context_length': model.get('context_length'),
                                'pricing': pricing,
                                'embedding_dimension': embedding_dimension
                            })
                    else:  # category == 'llm'
                        # Check for chat/completion support (exclude embedding-only models)
                        supports_chat = (
                            'text' in modalities or
                            'chat' in modalities or
                            capabilities.get('chat', True)  # Default to True if not specified
                        ) and not (
                            'embeddings' in modalities and len(modalities) == 1  # Embedding-only
                        )
                        if supports_chat:
                            filtered_models.append({
                                'id': model_id,
                                'name': model_name,
                                'description': model.get('description', ''),
                                'context_length': model.get('context_length'),
                                'pricing': pricing
                            })
                
                # Sort by name for better UX
                filtered_models.sort(key=lambda x: x['name'].lower())
                
                return jsonify({
                    "models": filtered_models,
                    "provider_type": provider_type,
                    "category": category
                }), 200
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching OpenRouter models: {e}")
                return jsonify({
                    "error": f"Failed to fetch models: {str(e)}",
                    "models": []
                }), 503
            except Exception as e:
                logger.error(f"Error processing OpenRouter models: {e}")
                return jsonify({
                    "error": f"Error processing models: {str(e)}",
                    "models": []
                }), 500
        
        # For other providers, return empty list (can be extended later)
        else:
            return jsonify({
                "models": [],
                "provider_type": provider_type,
                "category": category,
                "message": f"Model listing not yet supported for {provider_type}"
            }), 200
            
    except Exception as e:
        logger.error(f"Error getting provider models: {e}")
        return jsonify({"error": f"Failed to get models: {str(e)}"}), 500


@app.route('/settings/llm-providers/test', methods=['POST'])
@requires_write_auth
def test_llm_provider_endpoint():
    """Test LLM or embedding provider connection with provided configuration."""
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    data = request.json
    if data is None:
        return jsonify({"error": "Invalid or missing JSON body"}), 400
    
    try:
        provider_type = data.get('type')
        if not provider_type:
            return jsonify({"error": "Provider type is required"}), 400
        
        provider_category = data.get('category', 'llm')  # Default to 'llm' for backward compatibility
        if provider_category not in ['llm', 'embedding']:
            return jsonify({"error": "Provider category must be 'llm' or 'embedding'"}), 400
        
        config = data.get('config', {})
        # Allow empty dicts as factories use defaults; only reject None
        if config is None:
            return jsonify({"error": "Provider configuration is required"}), 400
        
        # Normalize config - ensure model is a string if it's an object
        # This handles cases where the frontend sends model as an object
        if isinstance(config, dict) and 'model' in config:
            model_value = config.get('model')
            
            # Check if model is the literal string "[object Object]" (JavaScript object conversion)
            if isinstance(model_value, str) and (model_value == '[object Object]' or '[object Object]' in model_value):
                logger.warning(f"Detected '[object Object]' string in model field, using default")
                if provider_type == 'openrouter' and provider_category == 'embedding':
                    config['model'] = 'openai/text-embedding-3-small'
                else:
                    config['model'] = None
            elif isinstance(model_value, dict):
                # Extract model string from object - try common fields
                extracted = (model_value.get('id') or 
                           model_value.get('name') or 
                           model_value.get('model') or
                           model_value.get('value') or
                           None)
                if extracted and isinstance(extracted, str) and extracted != '[object Object]':
                    config['model'] = extracted
                elif extracted and extracted != '[object Object]':
                    config['model'] = str(extracted)
                else:
                    # Fallback: try to get first string value from dict
                    found = False
                    for key, val in model_value.items():
                        if isinstance(val, str) and val and val != '[object Object]':
                            config['model'] = val
                            found = True
                            break
                    if not found:
                        # Last resort: use default based on provider
                        if provider_type == 'openrouter' and provider_category == 'embedding':
                            config['model'] = 'openai/text-embedding-3-small'
                        else:
                            config['model'] = None
            elif model_value is not None and not isinstance(model_value, str):
                # Convert to string if not already, but check for object conversion
                str_value = str(model_value)
                if str_value == '[object Object]' or '[object Object]' in str_value:
                    logger.warning(f"Model converted to '[object Object]', using default")
                    if provider_type == 'openrouter' and provider_category == 'embedding':
                        config['model'] = 'openai/text-embedding-3-small'
                    else:
                        config['model'] = None
                else:
                    config['model'] = str_value
            # If model is None or empty string and it's openrouter, set default
            elif provider_type == 'openrouter' and provider_category == 'embedding' and (not model_value or model_value == ''):
                config['model'] = 'openai/text-embedding-3-small'
        
        # Log the entire config for debugging
        logger.debug(f"Full config received: {redact_config(config)}")
        logger.debug(f"Model value: {config.get('model')}, type: {type(config.get('model')).__name__}")
        
        # Test provider connection based on category
        try:
            if provider_category == 'embedding':
                # Test embedding provider
                redacted_config = redact_config(config)
                logger.debug(f"Testing embedding provider {provider_type} with config model: {redacted_config.get('model')} (type: {type(config.get('model')).__name__})")
                # Force model to be a string one more time before passing to factory
                if 'model' in config:
                    model_val = config['model']
                    if isinstance(model_val, str) and (model_val == '[object Object]' or '[object Object]' in model_val):
                        logger.error(f"CRITICAL: Model is '[object Object]' string, replacing with default")
                        config['model'] = 'openai/text-embedding-3-small' if provider_type == 'openrouter' else None
                    elif not isinstance(model_val, str):
                        logger.error(f"CRITICAL: Model is not a string: {type(model_val).__name__}, value: {model_val}")
                        if isinstance(model_val, dict):
                            config['model'] = model_val.get('id') or model_val.get('name') or model_val.get('model') or 'openai/text-embedding-3-small'
                        else:
                            config['model'] = str(model_val) if model_val != '[object Object]' else 'openai/text-embedding-3-small'
                
                logger.debug(f"Final model before factory: {config.get('model')} (type: {type(config.get('model')).__name__})")
                
                # For OpenRouter, validate that the model supports embeddings
                if provider_type == 'openrouter' and config.get('model') and config.get('api_key'):
                    model_name = str(config.get('model'))
                    api_key = config.get('api_key')
                    
                    # Check if model supports embeddings by querying OpenRouter API
                    try:
                        headers = {
                            'Authorization': f'Bearer {api_key}',
                            'Content-Type': 'application/json'
                        }
                        response = requests.get('https://openrouter.ai/api/v1/models', headers=headers, timeout=10)
                        
                        if response.status_code == 200:
                            models_data = response.json()
                            all_models = models_data.get('data', [])
                            
                            # Find the model in the list
                            model_info = None
                            for m in all_models:
                                if m.get('id') == model_name:
                                    model_info = m
                                    break
                            
                            if model_info:
                                # Check if model supports embeddings - use strict check
                                modalities = model_info.get('modalities', [])
                                capabilities = model_info.get('capabilities', {})
                                
                                supports_embeddings = (
                                    'embeddings' in modalities or
                                    'embedding' in modalities or
                                    capabilities.get('embeddings', False)
                                ) or (
                                    # Only allow models with 'embedding' in name if they're known embedding models
                                    ('text-embedding' in model_name.lower() or 
                                     model_name.lower().endswith('-embed') or
                                     model_name.lower().startswith('embed-'))
                                )
                                
                                if not supports_embeddings:
                                    model_display_name = model_info.get('name', model_name)
                                    return jsonify({
                                        "success": False,
                                        "message": f"Model '{model_display_name}' ({model_name}) does not support embeddings. This is a chat/completion model, not an embedding model. Please use an embedding model like 'openai/text-embedding-3-small' (note: OpenRouter has no free embedding models - you'll need to use Ollama for free embeddings).",
                                        "error_type": "invalid_model"
                                    }), 400
                            else:
                                # Model not found - might be invalid, but proceed with test
                                logger.warning(f"Model '{model_name}' not found in OpenRouter models list, proceeding with test")
                    except Exception as e:
                        # If validation fails, log but don't block the test
                        logger.warning(f"Could not validate model embedding support: {e}, proceeding with test")
                
                embedding = EmbeddingProviderFactory.get_embeddings(provider_type, config)
                # Try to embed a simple test text
                test_response = embedding.embed_query("test")
                return jsonify({
                    "success": True,
                    "message": f"Successfully connected to {provider_type} embedding provider",
                    "test_response": f"Embedding generated (dimension: {len(test_response)})"
                }), 200
            else:
                # Test LLM provider
                llm = LLMProviderFactory.get_llm(provider_type, config)
                # Try to invoke with a simple test
                test_response = llm.invoke("Say 'test' if you can read this.")
                return jsonify({
                    "success": True,
                    "message": f"Successfully connected to {provider_type} LLM provider",
                    "test_response": str(test_response.content) if hasattr(test_response, 'content') else str(test_response)
                }), 200
        except Exception as e:
            logger.error(f"Provider test failed: {e}")
            provider_name = f"{provider_type} {provider_category} provider"
            return jsonify({
                "success": False,
                "message": f"Failed to connect to {provider_name}: {str(e)}"
            }), 503  # Return 503 Service Unavailable for connection failures
    except Exception as e:
        logger.error(f"Error testing provider: {e}")
        return jsonify({"error": f"Failed to test provider: {str(e)}"}), 500


@app.route('/confluence/test', methods=['POST'])
@requires_write_auth
def test_confluence_connection():
    """Test Confluence connection with provided credentials."""
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    data = request.json
    if data is None:
        return jsonify({"error": "Invalid or missing JSON body"}), 400
    
    try:
        # Validate required fields
        if 'url' not in data or not data['url']:
            return jsonify({"error": "URL is required"}), 400
        
        if 'instance_type' not in data or data['instance_type'] not in ['cloud', 'server']:
            return jsonify({"error": "instance_type must be 'cloud' or 'server'"}), 400
        
        # Create Confluence integration instance
        confluence = ConfluenceIntegration(
            url=data['url'],
            instance_type=data['instance_type'],
            api_token=data.get('api_token'),
            username=data.get('username'),
            password=data.get('password')
        )
        
        # Test connection
        result = confluence.test_connection()
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"Confluence connection test failed: {e}")
        return jsonify({
            "success": False,
            "message": f"Connection test failed: {str(e)}"
        }), 500


@app.route('/confluence/fetch', methods=['POST'])
@requires_write_auth
def fetch_confluence_pages():
    """Fetch and embed Confluence pages."""
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    data = request.json
    if data is None:
        return jsonify({"error": "Invalid or missing JSON body"}), 400
    
    try:
        # Get page IDs from request or from saved settings
        page_ids = data.get('page_ids', [])
        if not page_ids:
            # Try to get from saved settings
            settings = get_confluence_settings()
            page_ids = settings.get('page_ids', [])
        
        if not page_ids:
            return jsonify({"error": "No page IDs provided"}), 400
        
        # Get Confluence config from request or saved settings
        confluence_config = data.get('confluence_config')
        if not confluence_config:
            # Get from saved settings
            settings = get_confluence_settings()
            if not settings.get('url'):
                return jsonify({"error": "Confluence not configured. Please configure in Settings first."}), 400
            confluence_config = {
                'url': settings['url'],
                'instance_type': settings.get('instance_type', 'cloud'),
                'api_token': settings.get('api_token'),
                'username': settings.get('username'),
                'password': settings.get('password')
            }
        
        # Optional parameters
        collection_name = data.get('collection_name')
        version = data.get('version')
        overwrite = data.get('overwrite', False)
        
        # Embed pages
        results = embed_confluence_pages(
            page_ids=page_ids,
            confluence_config=confluence_config,
            collection_name=collection_name,
            version=version,
            overwrite=overwrite
        )
        
        return jsonify({
            "message": f"Processed {len(page_ids)} pages",
            "results": results
        }), 200
    except Exception as e:
        logger.error(f"Failed to fetch Confluence pages: {e}")
        return jsonify({"error": f"Failed to fetch pages: {str(e)}"}), 500


@app.route('/confluence/import', methods=['POST'])
@requires_write_auth
def import_confluence_page():
    """Import a single Confluence page to vector database using confluence-markdown-exporter."""
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    data = request.json
    if data is None:
        return jsonify({"error": "Invalid or missing JSON body"}), 400
    
    try:
        page_id = data.get('page_id')
        # Validate page_id is a string and not empty
        if not isinstance(page_id, str) or not page_id:
            return jsonify({"error": "page_id is required and must be a string"}), 400
        
        version = data.get('version')
        collection_name = data.get('collection_name')  # Optional collection name parameter
        # Convert overwrite to boolean, handling string values "true"/"false" and boolean values
        overwrite_value = data.get('overwrite', False)
        if isinstance(overwrite_value, str):
            overwrite = overwrite_value.lower() in ('true', '1', 'yes', 'on')
        else:
            overwrite = bool(overwrite_value)
        
        # Import the page
        result = import_confluence_page_to_vector_db(
            page_id=page_id,
            collection_name=collection_name,
            version=version,
            overwrite=overwrite
        )
        
        return jsonify(result), 200
    except ValueError as e:
        logger.error(f"Validation error importing Confluence page: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Failed to import Confluence page: {e}")
        return jsonify({"error": f"Failed to import page: {str(e)}"}), 500


if __name__ == '__main__':
    port = int(os.getenv('API_PORT', 8080))
    host = os.getenv('API_HOST', 'localhost')
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting RAG API server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)

