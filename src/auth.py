"""
Authentication Module
Provides username/password authentication with session management.
"""
import os
import hmac
import hashlib
import time
from functools import wraps
from flask import request, jsonify, session
from dotenv import load_dotenv
from .utils import setup_logging

load_dotenv()

logger = setup_logging()

# Authentication configuration
AUTH_ENABLED = os.getenv('AUTH_ENABLED', 'true').lower() == 'true'
AUTH_REQUIRED_FOR = os.getenv('AUTH_REQUIRED_FOR', 'write').lower()  # 'all', 'write', 'none'

# Hardcoded credentials (for now)
VALID_USERNAME = 'admin'
VALID_PASSWORD = '123QWEasd'


def generate_api_key() -> str:
    """
    Generate a new API key.
    
    Returns:
        str: A secure random API key
    """
    import secrets
    return secrets.token_urlsafe(32)


def verify_credentials(username: str, password: str) -> bool:
    """
    Verify username and password.
    
    Args:
        username: The username to verify
        password: The password to verify
        
    Returns:
        bool: True if credentials are valid
    """
    # Use constant-time comparison to prevent timing attacks
    username_valid = hmac.compare_digest(username, VALID_USERNAME)
    password_valid = hmac.compare_digest(password, VALID_PASSWORD)
    return username_valid and password_valid


def is_authenticated() -> bool:
    """
    Check if the current session is authenticated.
    
    Returns:
        bool: True if user is authenticated
    """
    return session.get('authenticated', False) and session.get('username') == VALID_USERNAME


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
        
        if not is_authenticated():
            return jsonify({
                "error": "Authentication required",
                "message": "Please log in to access this resource"
            }), 401
        
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
            if not is_authenticated():
                return jsonify({
                    "error": "Authentication required",
                    "message": "Please log in to access this resource"
                }), 401
        
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
        "authenticated": is_authenticated()
    }

