"""
Settings Storage Module
Manages storage and retrieval of application settings, including Confluence configuration.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from .utils import setup_logging

load_dotenv()

SETTINGS_DIR = Path(os.getenv('SETTINGS_DIR', './.rag_settings'))
CONFLUENCE_SETTINGS_FILE = SETTINGS_DIR / 'confluence.json'

logger = setup_logging()


def get_confluence_settings() -> Dict[str, Any]:
    """
    Load Confluence settings from file.
    
    Returns:
        dict: Confluence settings with default values if file doesn't exist
    """
    default_settings = {
        "enabled": False,
        "url": "",
        "instance_type": "cloud",  # "cloud" or "server"
        "api_token": "",
        "username": "",  # For server
        "password": "",  # For server (stored as plain text - consider encryption in production)
        "page_ids": [],
        "auto_sync": False,
        "sync_interval": 3600  # seconds
    }
    
    if not CONFLUENCE_SETTINGS_FILE.exists():
        logger.info("Confluence settings file not found, using defaults")
        return default_settings
    
    try:
        with open(CONFLUENCE_SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
            # Merge with defaults to ensure all keys exist
            merged = {**default_settings, **settings}
            return merged
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Error loading Confluence settings: {e}")
        return default_settings


def save_confluence_settings(settings: Dict[str, Any]) -> bool:
    """
    Save Confluence settings to file.
    
    Args:
        settings: Dictionary containing Confluence settings
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Ensure all required keys are present
        default_settings = {
            "enabled": False,
            "url": "",
            "instance_type": "cloud",
            "api_token": "",
            "username": "",
            "password": "",
            "page_ids": [],
            "auto_sync": False,
            "sync_interval": 3600
        }
        
        # Merge with defaults to ensure all keys exist
        merged_settings = {**default_settings, **settings}
        
        with open(CONFLUENCE_SETTINGS_FILE, 'w') as f:
            json.dump(merged_settings, f, indent=2)
        
        logger.info("Confluence settings saved successfully")
        return True
    except IOError as e:
        logger.error(f"Error saving Confluence settings: {e}")
        return False

