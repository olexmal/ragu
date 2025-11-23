"""
Authentication Module
Provides API authentication support (optional).
"""
import os
import hmac
import hashlib
import time
from functools import wraps
from flask import request, jsonify
from dotenv import load_dotenv
from .utils import setup_logging

load_dotenv()

logger = setup_logging()

# Authentication configuration
API_KEY = os.getenv('API_KEY', None)
API_KEY_HEADER = os.getenv('API_KEY_HEADER', 'X-API-Key')
AUTH_ENABLED = os.getenv('AUTH_ENABLED', 'false').lower() == 'true'
AUTH_REQUIRED_FOR = os.getenv('AUTH_REQUIRED_FOR', 'write').lower()  # 'all', 'write', 'none'


def generate_api_key() -> str:
    """
    Generate a new API key.
    
    Returns:
        str: A secure random API key
    """
    import secrets
    return secrets.token_urlsafe(32)


def verify_api_key(provided_key: str) -> bool:
    """
    Verify an API key.
    
    Args:
        provided_key: The API key to verify
        
    Returns:
        bool: True if key is valid
    """
    if not API_KEY:
        return False
    
    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(provided_key, API_KEY)


def requires_auth(f):
    """
    Decorator to require authentication for an endpoint.
    
    Usage:
        @app.route('/protected')
        @requires_auth
        def protected_endpoint():
            return jsonify({"message": "Protected"})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not AUTH_ENABLED:
            return f(*args, **kwargs)
        
        # Get API key from header
        api_key = request.headers.get(API_KEY_HEADER)
        
        if not api_key:
            return jsonify({
                "error": "Authentication required",
                "message": f"Missing {API_KEY_HEADER} header"
            }), 401
        
        if not verify_api_key(api_key):
            return jsonify({
                "error": "Authentication failed",
                "message": "Invalid API key"
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def requires_write_auth(f):
    """
    Decorator to require authentication only for write operations.
    Read operations are allowed without auth if AUTH_REQUIRED_FOR is 'write'.
    
    Usage:
        @app.route('/query', methods=['GET', 'POST'])
        @requires_write_auth
        def query_endpoint():
            # GET doesn't require auth, POST does
            return f(*args, **kwargs)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not AUTH_ENABLED:
            return f(*args, **kwargs)
        
        # Check if this is a write operation
        is_write = request.method in ['POST', 'PUT', 'PATCH', 'DELETE']
        
        # If auth is required for all, or this is a write operation
        if AUTH_REQUIRED_FOR == 'all' or (AUTH_REQUIRED_FOR == 'write' and is_write):
            api_key = request.headers.get(API_KEY_HEADER)
            
            if not api_key:
                return jsonify({
                    "error": "Authentication required",
                    "message": f"Missing {API_KEY_HEADER} header"
                }), 401
            
            if not verify_api_key(api_key):
                return jsonify({
                    "error": "Authentication failed",
                    "message": "Invalid API key"
                }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def get_auth_status() -> dict:
    """
    Get authentication configuration status.
    
    Returns:
        dict: Authentication status information
    """
    return {
        "enabled": AUTH_ENABLED,
        "required_for": AUTH_REQUIRED_FOR,
        "api_key_configured": API_KEY is not None,
        "header_name": API_KEY_HEADER
    }

