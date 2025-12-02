"""
Timeout Decorator for Request Handlers
Adds timeout functionality to prevent long-running operations from blocking threads.
"""
import signal
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import threading


class TimeoutError(Exception):
    """Custom timeout exception."""
    pass


def timeout(seconds):
    """
    Decorator to add timeout to a function.
    
    Args:
        seconds: Timeout in seconds
        
    Returns:
        Decorated function that raises TimeoutError if execution exceeds timeout
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Use ThreadPoolExecutor for timeout in a thread-safe way
            executor = ThreadPoolExecutor(max_workers=1)
            future = executor.submit(func, *args, **kwargs)
            
            try:
                result = future.result(timeout=seconds)
                return result
            except FuturesTimeoutError:
                future.cancel()
                raise TimeoutError(f"Operation timed out after {seconds} seconds")
            finally:
                executor.shutdown(wait=False)
        
        return wrapper
    return decorator


def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Operation timed out")


def timeout_signal(seconds):
    """
    Decorator using signal.alarm (Unix only, not thread-safe).
    Use timeout() instead for multi-threaded environments.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Only use signal on Unix systems and in main thread
            if hasattr(signal, 'SIGALRM') and threading.current_thread() is threading.main_thread():
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(seconds)
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)
            else:
                # Fallback to ThreadPoolExecutor for Windows or non-main threads
                return timeout(seconds)(func)(*args, **kwargs)
        
        return wrapper
    return decorator

