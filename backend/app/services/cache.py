"""Simple in-memory caching service."""

import time
from typing import Any, Optional, Dict
from functools import wraps
import hashlib
import json


class CacheService:
    """In-memory cache with TTL support."""
    
    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = 300  # 5 minutes
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a cache key from arguments."""
        key_parts = [prefix]
        
        # Add args
        for arg in args:
            if isinstance(arg, (dict, list)):
                key_parts.append(json.dumps(arg, sort_keys=True))
            else:
                key_parts.append(str(arg))
        
        # Add kwargs
        for k, v in sorted(kwargs.items()):
            if isinstance(v, (dict, list)):
                key_parts.append(f"{k}={json.dumps(v, sort_keys=True)}")
            else:
                key_parts.append(f"{k}={v}")
        
        # Create hash for long keys
        key_str = ":".join(key_parts)
        if len(key_str) > 250:
            key_hash = hashlib.md5(key_str.encode()).hexdigest()
            return f"{prefix}:{key_hash}"
        
        return key_str
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        
        # Check if expired
        if time.time() > entry["expires_at"]:
            del self.cache[key]
            return None
        
        return entry["value"]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        if ttl is None:
            ttl = self.default_ttl
        
        self.cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl,
            "created_at": time.time()
        }
    
    def delete(self, key: str) -> None:
        """Delete key from cache."""
        self.cache.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time > entry["expires_at"]
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        return len(expired_keys)


def cached(ttl: Optional[int] = None, prefix: Optional[str] = None):
    """
    Decorator for caching async function results.
    
    Args:
        ttl: Time to live in seconds
        prefix: Cache key prefix (defaults to function name)
    """
    def decorator(func):
        cache_prefix = prefix or func.__name__
        
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Generate cache key
            cache_key = cache_service._generate_key(cache_prefix, *args, **kwargs)
            
            # Check cache
            cached_value = cache_service.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function
            result = await func(self, *args, **kwargs)
            
            # Cache result
            cache_service.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    
    return decorator


# Global cache instance
cache_service = CacheService()