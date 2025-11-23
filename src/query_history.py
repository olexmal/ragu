"""
Query History Module
Tracks and manages query history with favorites support.
"""
import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from .utils import setup_logging

load_dotenv()

HISTORY_DIR = Path(os.getenv('HISTORY_DIR', './.rag_history'))
HISTORY_FILE = HISTORY_DIR / 'queries.json'
FAVORITES_FILE = HISTORY_DIR / 'favorites.json'
MAX_HISTORY = int(os.getenv('MAX_HISTORY', 1000))

logger = setup_logging()


class QueryHistory:
    """Manage query history and favorites."""
    
    def __init__(self):
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        self.history_file = HISTORY_FILE
        self.favorites_file = FAVORITES_FILE
        self._load_history()
        self._load_favorites()
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """Load query history from file."""
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error loading history: {e}")
            return []
    
    def _save_history(self, history: List[Dict[str, Any]]):
        """Save query history to file."""
        try:
            # Keep only last MAX_HISTORY entries
            history = history[-MAX_HISTORY:]
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except IOError as e:
            logger.error(f"Error saving history: {e}")
    
    def _load_favorites(self) -> List[str]:
        """Load favorites list from file."""
        if not self.favorites_file.exists():
            return []
        
        try:
            with open(self.favorites_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error loading favorites: {e}")
            return []
    
    def _save_favorites(self, favorites: List[str]):
        """Save favorites list to file."""
        try:
            with open(self.favorites_file, 'w') as f:
                json.dump(favorites, f, indent=2)
        except IOError as e:
            logger.error(f"Error saving favorites: {e}")
    
    def add_query(self, query: str, answer: str = None, version: str = None,
                  response_time: float = None, source_count: int = 0):
        """
        Add a query to history.
        
        Args:
            query: The query string
            answer: The answer received (optional)
            version: Version queried (optional)
            response_time: Response time in seconds (optional)
            source_count: Number of sources (optional)
        """
        history = self._load_history()
        
        entry = {
            'id': len(history) + 1,
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'answer': answer,
            'version': version,
            'response_time': response_time,
            'source_count': source_count
        }
        
        history.append(entry)
        self._save_history(history)
        logger.debug(f"Added query to history: {query[:50]}...")
    
    def get_history(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get query history.
        
        Args:
            limit: Maximum number of entries to return
            offset: Offset for pagination
            
        Returns:
            List of history entries
        """
        history = self._load_history()
        # Return in reverse chronological order
        return list(reversed(history[offset:offset+limit]))
    
    def search_history(self, search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search query history by query text.
        
        Args:
            search_term: Term to search for
            limit: Maximum number of results
            
        Returns:
            List of matching history entries
        """
        history = self._load_history()
        search_term_lower = search_term.lower()
        
        matches = [
            entry for entry in history
            if search_term_lower in entry.get('query', '').lower()
        ]
        
        return list(reversed(matches[-limit:]))
    
    def add_favorite(self, query: str):
        """Add a query to favorites."""
        favorites = self._load_favorites()
        if query not in favorites:
            favorites.append(query)
            self._save_favorites(favorites)
            logger.info(f"Added to favorites: {query[:50]}...")
    
    def remove_favorite(self, query: str):
        """Remove a query from favorites."""
        favorites = self._load_favorites()
        if query in favorites:
            favorites.remove(query)
            self._save_favorites(favorites)
            logger.info(f"Removed from favorites: {query[:50]}...")
    
    def get_favorites(self) -> List[str]:
        """Get list of favorite queries."""
        return self._load_favorites()
    
    def is_favorite(self, query: str) -> bool:
        """Check if a query is in favorites."""
        return query in self._load_favorites()
    
    def clear_history(self):
        """Clear all query history."""
        self._save_history([])
        logger.info("Query history cleared")
    
    def export_history(self, format: str = 'json') -> str:
        """
        Export query history.
        
        Args:
            format: Export format ('json' or 'csv')
            
        Returns:
            Exported data as string
        """
        history = self._load_history()
        
        if format == 'json':
            return json.dumps(history, indent=2)
        elif format == 'csv':
            import csv
            import io
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=['id', 'timestamp', 'query', 'version', 
                                                       'response_time', 'source_count'])
            writer.writeheader()
            for entry in history:
                writer.writerow({
                    'id': entry.get('id', ''),
                    'timestamp': entry.get('timestamp', ''),
                    'query': entry.get('query', ''),
                    'version': entry.get('version', ''),
                    'response_time': entry.get('response_time', ''),
                    'source_count': entry.get('source_count', '')
                })
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")


# Global history instance
_history_instance: Optional[QueryHistory] = None


def get_query_history() -> QueryHistory:
    """Get global query history instance."""
    global _history_instance
    if _history_instance is None:
        _history_instance = QueryHistory()
    return _history_instance

