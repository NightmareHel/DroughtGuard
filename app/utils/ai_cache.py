"""
Simple TTL cache for AI Advisor responses.
"""

import threading
from typing import Optional, Tuple
from cachetools import TTLCache


class SimpleCache:
    """Thread-safe TTL cache for AI responses."""
    
    def __init__(self, maxsize: int = 512, ttl_seconds: int = 86400):
        """
        Initialize cache.
        
        Args:
            maxsize: Maximum cache size
            ttl_seconds: Time-to-live in seconds (default 24 hours)
        """
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl_seconds)
        self._lock = threading.Lock()
    
    def get(self, key: Tuple) -> Optional[dict]:
        """Get value from cache."""
        with self._lock:
            return self._cache.get(key)
    
    def set(self, key: Tuple, value: dict, ttl_seconds: Optional[int] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Cache value
            ttl_seconds: Optional TTL override
        """
        with self._lock:
            if ttl_seconds is not None:
                # Create a new cache with custom TTL for this key
                # Note: cachetools doesn't support per-key TTL, so we store ttl in value
                value['_ttl'] = ttl_seconds
            
            self._cache[key] = value
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)


# Global cache instance
ai_cache = SimpleCache()

