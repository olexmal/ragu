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
SYSTEM_SETTINGS_FILE = SETTINGS_DIR / 'system.json'
LLM_PROVIDERS_FILE = SETTINGS_DIR / 'llm_providers.json'

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


def get_system_settings() -> Dict[str, Any]:
    """
    Load system settings from file.
    
    Returns:
        dict: System settings with default values if file doesn't exist
    """
    default_settings = {
        "system_name": "RAG System"
    }
    
    if not SYSTEM_SETTINGS_FILE.exists():
        logger.info("System settings file not found, using defaults")
        return default_settings
    
    try:
        with open(SYSTEM_SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
            # Merge with defaults to ensure all keys exist
            merged = {**default_settings, **settings}
            return merged
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Error loading system settings: {e}")
        return default_settings


def save_system_settings(settings: Dict[str, Any]) -> bool:
    """
    Save system settings to file.
    
    Args:
        settings: Dictionary containing system settings
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Ensure all required keys are present
        default_settings = {
            "system_name": "RAG System"
        }
        
        # Merge with defaults to ensure all keys exist
        merged_settings = {**default_settings, **settings}
        
        with open(SYSTEM_SETTINGS_FILE, 'w') as f:
            json.dump(merged_settings, f, indent=2)
        
        logger.info("System settings saved successfully")
        return True
    except IOError as e:
        logger.error(f"Error saving system settings: {e}")
        return False


def get_llm_providers() -> Dict[str, Any]:
    """
    Load LLM provider settings from file.
    
    Returns:
        dict: LLM provider settings with default Ollama configuration if file doesn't exist
    """
    default_settings = {
        "llm_providers": {
            "ollama": {
                "enabled": True,
                "is_active": True,
                "type": "ollama",
                "model": os.getenv('LLM_MODEL', 'mistral'),
                "base_url": os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),
                "temperature": 0
            }
        },
        "embedding_providers": {
            "ollama": {
                "enabled": True,
                "is_active": True,
                "type": "ollama",
                "model": os.getenv('TEXT_EMBEDDING_MODEL', 'nomic-embed-text'),
                "base_url": os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
            }
        }
    }
    
    if not LLM_PROVIDERS_FILE.exists():
        logger.info("LLM providers settings file not found, using defaults")
        return default_settings
    
    try:
        with open(LLM_PROVIDERS_FILE, 'r') as f:
            settings = json.load(f)
            # Ensure structure exists
            if 'llm_providers' not in settings:
                settings['llm_providers'] = default_settings['llm_providers']
            if 'embedding_providers' not in settings:
                settings['embedding_providers'] = default_settings['embedding_providers']
            
            # Ensure at least one active provider exists
            llm_active = any(p.get('is_active', False) and p.get('enabled', False) for p in settings['llm_providers'].values())
            if not llm_active and 'ollama' in settings['llm_providers']:
                settings['llm_providers']['ollama']['is_active'] = True
                settings['llm_providers']['ollama']['enabled'] = True
            
            emb_active = any(p.get('is_active', False) and p.get('enabled', False) for p in settings['embedding_providers'].values())
            if not emb_active and 'ollama' in settings['embedding_providers']:
                settings['embedding_providers']['ollama']['is_active'] = True
                settings['embedding_providers']['ollama']['enabled'] = True
            
            return settings
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Error loading LLM provider settings: {e}")
        return default_settings


def save_llm_providers(settings: Dict[str, Any]) -> bool:
    """
    Save LLM provider settings to file.
    
    Args:
        settings: Dictionary containing LLM provider settings
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Validate structure
        if 'llm_providers' not in settings:
            raise ValueError("llm_providers key is required")
        if 'embedding_providers' not in settings:
            raise ValueError("embedding_providers key is required")
        
        # Ensure only one active LLM provider
        active_llm_count = sum(1 for p in settings['llm_providers'].values() if p.get('is_active', False) and p.get('enabled', False))
        if active_llm_count == 0:
            # If no active, make ollama active and enabled if it exists, otherwise create it
            if 'ollama' in settings['llm_providers']:
                settings['llm_providers']['ollama']['is_active'] = True
                settings['llm_providers']['ollama']['enabled'] = True
            else:
                # Create default Ollama provider if it doesn't exist
                settings['llm_providers']['ollama'] = {
                    "enabled": True,
                    "is_active": True,
                    "type": "ollama",
                    "model": os.getenv('LLM_MODEL', 'mistral'),
                    "base_url": os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),
                    "temperature": 0
                }
        elif active_llm_count > 1:
            # If multiple active, keep only the first enabled and active one
            found_first = False
            for key, provider in settings['llm_providers'].items():
                if provider.get('is_active', False) and provider.get('enabled', False):
                    if found_first:
                        provider['is_active'] = False
                    else:
                        found_first = True
                elif provider.get('is_active', False):
                    # Deactivate providers that are active but disabled
                    provider['is_active'] = False
        
        # Ensure only one active embedding provider
        active_emb_count = sum(1 for p in settings['embedding_providers'].values() if p.get('is_active', False) and p.get('enabled', False))
        if active_emb_count == 0:
            # If no active, make ollama active and enabled if it exists, otherwise create it
            if 'ollama' in settings['embedding_providers']:
                settings['embedding_providers']['ollama']['is_active'] = True
                settings['embedding_providers']['ollama']['enabled'] = True
            else:
                # Create default Ollama provider if it doesn't exist
                settings['embedding_providers']['ollama'] = {
                    "enabled": True,
                    "is_active": True,
                    "type": "ollama",
                    "model": os.getenv('TEXT_EMBEDDING_MODEL', 'nomic-embed-text'),
                    "base_url": os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
                }
        elif active_emb_count > 1:
            # If multiple active, keep only the first enabled and active one
            found_first = False
            for key, provider in settings['embedding_providers'].items():
                if provider.get('is_active', False) and provider.get('enabled', False):
                    if found_first:
                        provider['is_active'] = False
                    else:
                        found_first = True
                elif provider.get('is_active', False):
                    # Deactivate providers that are active but disabled
                    provider['is_active'] = False
        
        with open(LLM_PROVIDERS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        
        logger.info("LLM provider settings saved successfully")
        return True
    except (IOError, ValueError) as e:
        logger.error(f"Error saving LLM provider settings: {e}")
        return False


def get_active_llm_provider() -> Dict[str, Any]:
    """
    Get the currently active LLM provider configuration.
    
    Returns:
        dict: Active LLM provider configuration, or default Ollama if none found
    """
    providers = get_llm_providers()
    
    for provider_key, provider_config in providers['llm_providers'].items():
        if provider_config.get('is_active', False) and provider_config.get('enabled', False):
            return provider_config
    
    # Fallback to Ollama default
    return {
        "enabled": True,
        "is_active": True,
        "type": "ollama",
        "model": os.getenv('LLM_MODEL', 'mistral'),
        "base_url": os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),
        "temperature": 0
    }


def get_active_embedding_provider() -> Dict[str, Any]:
    """
    Get the currently active embedding provider configuration.
    
    Returns:
        dict: Active embedding provider configuration, or default Ollama if none found
    """
    providers = get_llm_providers()
    
    for provider_key, provider_config in providers['embedding_providers'].items():
        if provider_config.get('is_active', False) and provider_config.get('enabled', False):
            return provider_config
    
    # Fallback to Ollama default
    return {
        "enabled": True,
        "is_active": True,
        "type": "ollama",
        "model": os.getenv('TEXT_EMBEDDING_MODEL', 'nomic-embed-text'),
        "base_url": os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    }

