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


def generate_collection_name(base_name, version=None):
    """
    Generate collection name with optional version suffix.
    
    Args:
        base_name: Base collection name
        version: Optional version string
        
    Returns:
        str: Collection name
    """
    if version:
        return f"{base_name}-v{version}"
    return base_name


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
    """
    import logging
    
    formatter = RedactingFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    file_handler = logging.FileHandler('ragu.log')
    file_handler.setFormatter(formatter)
    
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, stream_handler]
    )
    
    return logging.getLogger(__name__)

