"""
Utility Functions
Helper functions for common operations.
"""
import os
import subprocess
import re
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

MAVEN_POM_PATH = os.getenv('MAVEN_POM_PATH', '../pom.xml')
COMMON_MODEL_VERSION_PROPERTY = os.getenv('COMMON_MODEL_VERSION_PROPERTY', 'commonmodel.version')


def get_maven_version():
    """
    Resolve current common model version from Maven property.
    
    Returns:
        str: Version string or None if not found
    """
    try:
        result = subprocess.run(
            ['mvn', 'help:evaluate', 
             f'-Dexpression={COMMON_MODEL_VERSION_PROPERTY}', 
             '-q', '-DforceStdout'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(MAVEN_POM_PATH) if os.path.dirname(MAVEN_POM_PATH) else '.'
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            return version if version else None
    except Exception as e:
        print(f"Error resolving Maven version: {e}")
    return None


def detect_document_format(file_path):
    """
    Detect document format from file extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: Document format ('pdf', 'html', 'txt', 'md', 'unknown')
    """
    ext = Path(file_path).suffix.lower()
    format_map = {
        '.pdf': 'pdf',
        '.html': 'html',
        '.htm': 'html',
        '.txt': 'txt',
        '.md': 'md',
        '.markdown': 'md'
    }
    return format_map.get(ext, 'unknown')


def extract_version_from_path(path):
    """
    Extract version string from file or directory path.
    
    Args:
        path: File or directory path
        
    Returns:
        str: Version string or None
    """
    # Look for version patterns like v1.2.3, 1.2.3, version-1.2.3
    version_pattern = r'(?:v|version[-_]?)?(\d+\.\d+\.\d+(?:[-\.]\w+)?)'
    match = re.search(version_pattern, path, re.IGNORECASE)
    return match.group(1) if match else None


def sanitize_collection_name(name: str) -> str:
    """
    Sanitize collection name to meet ChromaDB requirements.
    
    ChromaDB requires:
    - 3-512 characters
    - Only [a-zA-Z0-9._-]
    - Must start and end with [a-zA-Z0-9] (not underscore, dot, or hyphen)
    
    Args:
        name: Collection name to sanitize
        
    Returns:
        str: Sanitized collection name
    """
    if not name:
        return "collection"
    
    # Replace spaces and other invalid characters with underscores
    import re
    # Replace spaces and special chars (except allowed ones) with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', name)
    
    # Remove leading/trailing dots, underscores, and hyphens
    sanitized = sanitized.strip('._-')
    
    # Ensure it starts and ends with alphanumeric
    if not sanitized or not sanitized[0].isalnum():
        sanitized = 'c' + sanitized
    if not sanitized[-1].isalnum():
        sanitized = sanitized + '1'
    
    # Ensure minimum length of 3
    if len(sanitized) < 3:
        sanitized = sanitized.ljust(3, '0')
    
    # Truncate if too long (ChromaDB max is 512)
    if len(sanitized) > 512:
        sanitized = sanitized[:509]  # Leave room for suffix
        # Ensure it ends with alphanumeric
        if not sanitized[-1].isalnum():
            sanitized = sanitized[:-1] + '1'
    
    return sanitized


def generate_collection_name(base_name, version=None):
    """
    Generate collection name with optional version suffix.
    Sanitizes the name to meet ChromaDB requirements.
    
    Args:
        base_name: Base collection name (e.g., 'Angular', 'React')
        version: Optional version string (e.g., 'v19', '2.0')
        
    Returns:
        str: Sanitized collection name (e.g., 'Angular-v19')
    
    Examples:
        generate_collection_name('Angular', 'v19') -> 'Angular-v19'
        generate_collection_name('Angular', '19') -> 'Angular-v19'
        generate_collection_name('Angular v19', None) -> 'Angular_v19'
        generate_collection_name('Angular v19', 'v19') -> 'Angular-v19' (deduplicates)
    """
    import re
    
    # Sanitize base name first
    sanitized_base = sanitize_collection_name(base_name)
    
    if version:
        # Sanitize version - only replace invalid characters, don't apply min length
        # (min length will be satisfied by the combined name)
        sanitized_version = re.sub(r'[^a-zA-Z0-9._-]', '_', version).strip('._-')
        
        # Normalize version for comparison (ensure it has 'v' prefix)
        normalized_version = sanitized_version
        if sanitized_version and sanitized_version[0].lower() != 'v':
            normalized_version = f"v{sanitized_version}"
        
        # Check if base name already ends with the version (to avoid duplication)
        # e.g., "Angular_v19" with version "v19" should become "Angular-v19", not "Angular_v19-v19"
        base_lower = sanitized_base.lower()
        version_lower = normalized_version.lower()
        
        # Check for various patterns where version might already be in the base name
        # Pattern 1: base ends with "_v19" or "-v19" and version is "v19"
        # Pattern 2: base ends with "_19" or "-19" and version is "19" or "v19"
        if base_lower.endswith(f"_{version_lower}") or base_lower.endswith(f"-{version_lower}"):
            # Version is already in the base name with separator, strip it and re-add properly
            # Find where the version starts
            if base_lower.endswith(f"_{version_lower}"):
                sanitized_base = sanitized_base[:-(len(version_lower) + 1)]  # Remove "_v19"
            elif base_lower.endswith(f"-{version_lower}"):
                sanitized_base = sanitized_base[:-(len(version_lower) + 1)]  # Remove "-v19"
        elif base_lower.endswith(version_lower):
            # Version is at the end without separator (unlikely but handle it)
            sanitized_base = sanitized_base[:-len(version_lower)].rstrip('_-')
        
        # Ensure base is still valid after stripping
        if len(sanitized_base) < 3:
            sanitized_base = sanitize_collection_name(sanitized_base)
        
        # Build final name with version
        if sanitized_version and sanitized_version[0].lower() == 'v':
            # Version already has 'v' prefix
            combined = f"{sanitized_base}-{sanitized_version}"
        else:
            # Add 'v' prefix for version
            combined = f"{sanitized_base}-v{sanitized_version}"
        
        return combined
    return sanitized_base


def redact_api_keys(text: str) -> str:
    """
    Redact API keys and sensitive information from text.
    
    Args:
        text: Text that may contain API keys
        
    Returns:
        str: Text with API keys redacted
    """
    import re
    
    # Pattern for OpenRouter API keys (sk-or-v1-...)
    text = re.sub(r'sk-or-v1-[a-zA-Z0-9]{40,}', 'sk-or-v1-***REDACTED***', text)
    
    # Pattern for OpenAI/Anthropic API keys (sk-...)
    text = re.sub(r'sk-[a-zA-Z0-9]{20,}', 'sk-***REDACTED***', text)
    
    # Pattern for generic API keys in query parameters
    text = re.sub(r'api_key=([^&\s]+)', r'api_key=***REDACTED***', text, flags=re.IGNORECASE)
    text = re.sub(r'apikey=([^&\s]+)', r'apikey=***REDACTED***', text, flags=re.IGNORECASE)
    
    # Pattern for Authorization headers
    text = re.sub(r'Authorization:\s*(?:Bearer\s+)?([^\s"]+)', r'Authorization: Bearer ***REDACTED***', text, flags=re.IGNORECASE)
    
    return text


def redact_config(config: dict) -> dict:
    """
    Redact sensitive fields from configuration dictionary.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        dict: Configuration with sensitive fields redacted
    """
    sensitive_keys = ['api_key', 'apiKey', 'apikey', 'password', 'token', 'secret', 'auth']
    redacted = config.copy()
    
    for key in redacted:
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            if isinstance(redacted[key], str) and len(redacted[key]) > 10:
                redacted[key] = '***REDACTED***'
    
    return redacted


class RedactingFormatter(logging.Formatter):
    """Custom formatter that redacts API keys from log messages."""
    
    def format(self, record):
        # Redact API keys from the message
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = redact_api_keys(record.msg)
        elif hasattr(record, 'msg'):
            record.msg = str(record.msg)
            record.msg = redact_api_keys(record.msg)
        
        # Redact from args if present
        if hasattr(record, 'args') and record.args:
            new_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    new_args.append(redact_api_keys(arg))
                elif isinstance(arg, dict):
                    new_args.append(redact_config(arg))
                else:
                    new_args.append(arg)
            record.args = tuple(new_args)
        
        return super().format(record)


def setup_logging():
    """
    Configure logging for the application with API key redaction.
    Logs are written to the logs directory (configurable via LOG_DIR env var).
    """
    import logging
    import os
    from pathlib import Path
    
    # Determine log directory - use environment variable or default to ./logs
    log_dir = Path(os.getenv('LOG_DIR', './logs'))
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Log file path
    log_file = log_dir / 'ragu.log'
    
    formatter = RedactingFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    file_handler = logging.FileHandler(str(log_file))
    file_handler.setFormatter(formatter)
    
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, stream_handler]
    )
    
    return logging.getLogger(__name__)

