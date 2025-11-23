"""
Flask API Server
RESTful API for embedding and querying documentation.
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
from pathlib import Path
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Handle imports for both module and standalone execution
if __name__ == '__main__':
    from embed import embed_file, embed_directory
    from query import query_docs, query_simple
    from utils import setup_logging
    # Multi-version and history not available in standalone mode
    query_multiple_versions = None
    compare_versions = None
    get_query_history = None
    requires_auth = lambda f: f  # No-op decorator
    requires_write_auth = lambda f: f
else:
    from .embed import embed_file, embed_directory
    from .query import query_docs, query_simple
    from .multi_version_query import query_multiple_versions, compare_versions
    from .query_history import get_query_history
    from .utils import setup_logging
    from .auth import requires_auth, requires_write_auth, get_auth_status
    from .code_extractor import extract_code_from_document, format_code_for_response

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Ensure temp directory exists
TEMP_DIR = Path(os.getenv('TEMP_FOLDER', './_temp'))
TEMP_DIR.mkdir(parents=True, exist_ok=True)

logger = setup_logging()


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    try:
        # Check if Ollama is accessible
        from langchain_ollama import ChatOllama
        llm = ChatOllama(model=os.getenv('LLM_MODEL', 'mistral'))
        # Simple test - just check if model is available
        
        # Include auth status if available
        auth_status = {}
        try:
            if get_auth_status:
                auth_status = get_auth_status()
        except:
            pass
        
        response = {
            "status": "healthy",
            "service": "RAG API",
            "ollama_available": True
        }
        response.update(auth_status)
        
        return jsonify(response), 200
    except Exception as e:
        return jsonify({
            "status": "degraded",
            "service": "RAG API",
            "ollama_available": False,
            "error": str(e)
        }), 503
    """Health check endpoint."""
    try:
        # Check if Ollama is accessible
        from langchain_ollama import ChatOllama
        llm = ChatOllama(model=os.getenv('LLM_MODEL', 'mistral'))
        # Simple test - just check if model is available
        return jsonify({
            "status": "healthy",
            "service": "RAG API",
            "ollama_available": True
        }), 200
    except Exception as e:
        return jsonify({
            "status": "degraded",
            "service": "RAG API",
            "ollama_available": False,
            "error": str(e)
        }), 503


@app.route('/embed', methods=['POST'])
@requires_write_auth
def embed():
    """Embed a single file into the vector database."""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    version = request.form.get('version')  # Optional version parameter
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
        # Embed with version support and incremental update capability
        embed_file(str(file_path), version=version, overwrite=overwrite)
        return jsonify({
            "message": "File embedded successfully",
            "version": version,
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
            version=version,
            overwrite=overwrite
        )
        return jsonify({
            "message": "Batch embedding completed",
            "results": results,
            "version": version
        }), 200
    except Exception as e:
        logger.error(f"Batch embedding failed: {e}")
        return jsonify({"error": f"Batch embedding failed: {str(e)}"}), 500


@app.route('/query', methods=['POST'])
def query():
    """Query the documentation using natural language."""
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
        if use_simple:
            result = query_simple(question, collection_name, version, k)
        else:
            result = query_docs(question, collection_name, version, k)
        
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
        
        response = {
            "answer": result.get('result', ''),
            "query": result.get('query', question),
            "sources": sources,
            "source_count": len(sources)
        }
        
        # Add to query history
        try:
            history = get_query_history()
            history.add_query(
                question,
                answer=result['result'],
                version=version,
                response_time=None,  # Could extract from result if available
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
def list_collections():
    """List all available collections."""
    try:
        import chromadb
        client = chromadb.PersistentClient(path=os.getenv('CHROMA_PATH', 'chroma'))
        collections = client.list_collections()
        
        collection_info = []
        for collection in collections:
            collection_info.append({
                "name": collection.name,
                "count": collection.count()
            })
        
        return jsonify({
            "collections": collection_info,
            "total": len(collection_info)
        }), 200
    except Exception as e:
        logger.error(f"Error listing collections: {e}")
        return jsonify({"error": f"Failed to list collections: {str(e)}"}), 500


@app.route('/collections/<version>', methods=['GET'])
def get_collection_info(version):
    """Get information about a specific collection."""
    try:
        import chromadb
        client = chromadb.PersistentClient(path=os.getenv('CHROMA_PATH', 'chroma'))
        collection_name = f"{os.getenv('COLLECTION_NAME', 'common-model-docs')}-v{version}"
        
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
def delete_collection(version):
    """Delete a specific collection."""
    try:
        import chromadb
        client = chromadb.PersistentClient(path=os.getenv('CHROMA_PATH', 'chroma'))
        collection_name = f"{os.getenv('COLLECTION_NAME', 'common-model-docs')}-v{version}"
        
        client.delete_collection(name=collection_name)
        
        return jsonify({
            "message": f"Collection {collection_name} deleted successfully",
            "version": version
        }), 200
    except Exception as e:
        logger.error(f"Error deleting collection: {e}")
        return jsonify({"error": f"Failed to delete collection: {str(e)}"}), 500


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


@app.route('/auth/status', methods=['GET'])
def auth_status():
    """Get authentication configuration status."""
    try:
        if get_auth_status:
            status = get_auth_status()
            return jsonify(status), 200
        else:
            return jsonify({
                "enabled": False,
                "message": "Authentication module not available"
            }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get auth status: {str(e)}"}), 500


if __name__ == '__main__':
    port = int(os.getenv('API_PORT', 8080))
    host = os.getenv('API_HOST', 'localhost')
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting RAG API server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)

