"""
Monitoring Module
Tracks query patterns, embedding operations, and system metrics.
"""
import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict
from dotenv import load_dotenv
from .utils import setup_logging

load_dotenv()

MONITORING_DIR = Path(os.getenv('MONITORING_DIR', './.rag_monitoring'))
MONITORING_ENABLED = os.getenv('MONITORING_ENABLED', 'true').lower() == 'true'

logger = setup_logging()


class QueryMonitor:
    """Monitor and track query patterns."""
    
    def __init__(self, monitoring_dir: Path = None):
        self.monitoring_dir = Path(monitoring_dir or MONITORING_DIR)
        self.monitoring_dir.mkdir(parents=True, exist_ok=True)
        self.queries_file = self.monitoring_dir / 'queries.jsonl'
        self.stats_file = self.monitoring_dir / 'stats.json'
    
    def log_query(self, query: str, version: str = None, response_time: float = None, 
                  source_count: int = 0, cached: bool = False):
        """
        Log a query for monitoring.
        
        Args:
            query: The query string
            version: Optional version string
            response_time: Query response time in seconds
            source_count: Number of source documents retrieved
            cached: Whether result was from cache
        """
        if not MONITORING_ENABLED:
            return
        
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'query': query,
                'version': version,
                'response_time': response_time,
                'source_count': source_count,
                'cached': cached
            }
            
            with open(self.queries_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        
        except Exception as e:
            logger.warning(f"Error logging query: {e}")
    
    def get_query_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        Get query statistics for the last N days.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with statistics
        """
        if not self.queries_file.exists():
            return {
                'total_queries': 0,
                'unique_queries': 0,
                'avg_response_time': 0,
                'cache_hit_rate': 0,
                'top_queries': []
            }
        
        try:
            cutoff_time = time.time() - (days * 24 * 60 * 60)
            queries = []
            query_counts = defaultdict(int)
            response_times = []
            cached_count = 0
            total_count = 0
            
            with open(self.queries_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        entry_time = datetime.fromisoformat(entry['timestamp']).timestamp()
                        
                        if entry_time >= cutoff_time:
                            queries.append(entry)
                            query_counts[entry['query'].lower()] += 1
                            if entry.get('response_time'):
                                response_times.append(entry['response_time'])
                            if entry.get('cached'):
                                cached_count += 1
                            total_count += 1
                    except (json.JSONDecodeError, KeyError):
                        continue
            
            # Calculate statistics
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            cache_hit_rate = (cached_count / total_count * 100) if total_count > 0 else 0
            
            # Top queries
            top_queries = sorted(query_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                'total_queries': total_count,
                'unique_queries': len(query_counts),
                'avg_response_time': round(avg_response_time, 3),
                'cache_hit_rate': round(cache_hit_rate, 2),
                'top_queries': [{'query': q, 'count': c} for q, c in top_queries],
                'period_days': days
            }
        
        except Exception as e:
            logger.error(f"Error calculating query stats: {e}")
            return {}


class EmbeddingMonitor:
    """Monitor embedding operations."""
    
    def __init__(self, monitoring_dir: Path = None):
        self.monitoring_dir = Path(monitoring_dir or MONITORING_DIR)
        self.monitoring_dir.mkdir(parents=True, exist_ok=True)
        self.embeddings_file = self.monitoring_dir / 'embeddings.jsonl'
    
    def log_embedding(self, file_path: str, version: str = None, 
                     collection_name: str = None, chunk_count: int = 0,
                     duration: float = None, success: bool = True):
        """
        Log an embedding operation.
        
        Args:
            file_path: Path to embedded file
            version: Optional version string
            collection_name: Collection name
            chunk_count: Number of chunks created
            duration: Embedding duration in seconds
            success: Whether operation succeeded
        """
        if not MONITORING_ENABLED:
            return
        
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'file_path': file_path,
                'version': version,
                'collection_name': collection_name,
                'chunk_count': chunk_count,
                'duration': duration,
                'success': success
            }
            
            with open(self.embeddings_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        
        except Exception as e:
            logger.warning(f"Error logging embedding: {e}")
    
    def get_embedding_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        Get embedding statistics for the last N days.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with statistics
        """
        if not self.embeddings_file.exists():
            return {
                'total_embeddings': 0,
                'successful': 0,
                'failed': 0,
                'total_chunks': 0,
                'avg_duration': 0
            }
        
        try:
            cutoff_time = time.time() - (days * 24 * 60 * 60)
            embeddings = []
            
            with open(self.embeddings_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        entry_time = datetime.fromisoformat(entry['timestamp']).timestamp()
                        
                        if entry_time >= cutoff_time:
                            embeddings.append(entry)
                    except (json.JSONDecodeError, KeyError):
                        continue
            
            successful = sum(1 for e in embeddings if e.get('success', True))
            failed = len(embeddings) - successful
            total_chunks = sum(e.get('chunk_count', 0) for e in embeddings)
            durations = [e.get('duration', 0) for e in embeddings if e.get('duration')]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            return {
                'total_embeddings': len(embeddings),
                'successful': successful,
                'failed': failed,
                'total_chunks': total_chunks,
                'avg_duration': round(avg_duration, 3),
                'period_days': days
            }
        
        except Exception as e:
            logger.error(f"Error calculating embedding stats: {e}")
            return {}


# Global monitor instances
_query_monitor: Optional[QueryMonitor] = None
_embedding_monitor: Optional[EmbeddingMonitor] = None


def get_query_monitor() -> QueryMonitor:
    """Get global query monitor instance."""
    global _query_monitor
    if _query_monitor is None:
        _query_monitor = QueryMonitor()
    return _query_monitor


def get_embedding_monitor() -> EmbeddingMonitor:
    """Get global embedding monitor instance."""
    global _embedding_monitor
    if _embedding_monitor is None:
        _embedding_monitor = EmbeddingMonitor()
    return _embedding_monitor

