"""
Query Caching Module
Caches frequently asked queries to improve performance.
"""
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from .utils import setup_logging

load_dotenv()

CACHE_DIR = Path(os.getenv('CACHE_DIR', './.rag_cache'))
CACHE_TTL = int(os.getenv('CACHE_TTL', 3600))  # Default: 1 hour
CACHE_MAX_SIZE = int(os.getenv('CACHE_MAX_SIZE', 100))  # Maximum number of cached queries

logger = setup_logging()


class QueryCache:
    """Simple file-based cache for query results."""
    
    def __init__(self, cache_dir: Path = None, ttl: int = None, max_size: int = None):
        self.cache_dir = Path(cache_dir or CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl or CACHE_TTL
        self.max_size = max_size or CACHE_MAX_SIZE
    
    def _get_cache_key(self, query: str, version: str = None, k: int = 3) -> str:
        """Generate cache key from query parameters."""
        cache_data = {
            'query': query.lower().strip(),
            'version': version,
            'k': k
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get file path for cache entry."""
        return self.cache_dir / f"{cache_key}.json"
    
    def get(self, query: str, version: str = None, k: int = 3) -> Optional[Dict[str, Any]]:
        """
        Get cached query result if available and not expired.
        
        Args:
            query: The query string
            version: Optional version string
            k: Number of documents retrieved
            
        Returns:
            Cached result dict or None if not found/expired
        """
        cache_key = self._get_cache_key(query, version, k)
        cache_path = self._get_cache_path(cache_key)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r') as f:
                cache_entry = json.load(f)
            
            # Check if cache entry is expired
            if time.time() - cache_entry['timestamp'] > self.ttl:
                logger.debug(f"Cache entry expired for query: {query[:50]}...")
                cache_path.unlink()
                return None
            
            logger.info(f"Cache hit for query: {query[:50]}...")
            return cache_entry['result']
        
        except (json.JSONDecodeError, KeyError, IOError) as e:
            logger.warning(f"Error reading cache entry: {e}")
            if cache_path.exists():
                cache_path.unlink()
            return None
    
    def set(self, query: str, result: Dict[str, Any], version: str = None, k: int = 3):
        """
        Cache a query result.
        
        Args:
            query: The query string
            result: The query result to cache
            version: Optional version string
            k: Number of documents retrieved
        """
        cache_key = self._get_cache_key(query, version, k)
        cache_path = self._get_cache_path(cache_key)
        
        # Enforce max cache size
        self._enforce_max_size()
        
        try:
            cache_entry = {
                'timestamp': time.time(),
                'query': query,
                'version': version,
                'k': k,
                'result': result
            }
            
            with open(cache_path, 'w') as f:
                json.dump(cache_entry, f, indent=2)
            
            logger.info(f"Cached query result: {query[:50]}...")
        
        except IOError as e:
            logger.warning(f"Error writing cache entry: {e}")
    
    def _enforce_max_size(self):
        """Remove oldest cache entries if cache exceeds max size."""
        cache_files = list(self.cache_dir.glob("*.json"))
        
        if len(cache_files) < self.max_size:
            return
        
        # Sort by modification time (oldest first)
        cache_files.sort(key=lambda p: p.stat().st_mtime)
        
        # Remove oldest entries
        to_remove = len(cache_files) - self.max_size + 1
        for cache_file in cache_files[:to_remove]:
            try:
                cache_file.unlink()
                logger.debug(f"Removed old cache entry: {cache_file.name}")
            except IOError as e:
                logger.warning(f"Error removing cache entry: {e}")
    
    def clear(self):
        """Clear all cache entries."""
        cache_files = list(self.cache_dir.glob("*.json"))
        for cache_file in cache_files:
            try:
                cache_file.unlink()
            except IOError:
                pass
        logger.info(f"Cleared {len(cache_files)} cache entries")
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            'entries': len(cache_files),
            'max_size': self.max_size,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'ttl_seconds': self.ttl
        }


# Global cache instance
_cache_instance: Optional[QueryCache] = None


def get_cache() -> QueryCache:
    """Get global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = QueryCache()
    return _cache_instance

