"""
Utility Functions
Helper functions for common operations.
"""
import os
import subprocess
import re
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


def setup_logging():
    """
    Configure logging for the application.
    """
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('ragu.log'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

