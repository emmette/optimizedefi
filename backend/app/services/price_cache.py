"""Price cache service for reducing API calls to 1inch."""

import asyncio
import time
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class PriceCache:
    """In-memory cache for token prices with TTL support."""
    
    def __init__(self, default_ttl: int = 60):
        """
        Initialize the price cache.
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 60s)
        """
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        
    def _make_key(self, chain_id: int, token_address: str) -> str:
        """Create a cache key from chain ID and token address."""
        return f"{chain_id}:{token_address.lower()}"
    
    async def get(self, chain_id: int, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Get cached price data for a token.
        
        Args:
            chain_id: Chain ID
            token_address: Token contract address
            
        Returns:
            Cached price data or None if not found/expired
        """
        async with self._lock:
            key = self._make_key(chain_id, token_address)
            entry = self._cache.get(key)
            
            if entry and entry["expires_at"] > time.time():
                logger.debug(f"Cache hit for {key}")
                return entry["data"]
            
            # Remove expired entry
            if entry:
                del self._cache[key]
                logger.debug(f"Cache expired for {key}")
            
            return None
    
    async def get_many(
        self, 
        chain_id: int, 
        token_addresses: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get cached prices for multiple tokens.
        
        Args:
            chain_id: Chain ID
            token_addresses: List of token contract addresses
            
        Returns:
            Dictionary of cached prices by token address
        """
        results = {}
        for address in token_addresses:
            cached = await self.get(chain_id, address)
            if cached:
                results[address.lower()] = cached
        return results
    
    async def set(
        self, 
        chain_id: int, 
        token_address: str, 
        price_data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> None:
        """
        Cache price data for a token.
        
        Args:
            chain_id: Chain ID
            token_address: Token contract address
            price_data: Price data to cache
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        async with self._lock:
            key = self._make_key(chain_id, token_address)
            ttl = ttl or self.default_ttl
            
            self._cache[key] = {
                "data": price_data,
                "expires_at": time.time() + ttl,
                "cached_at": time.time()
            }
            logger.debug(f"Cached price for {key} with TTL {ttl}s")
    
    async def set_many(
        self,
        chain_id: int,
        prices: Dict[str, Dict[str, Any]],
        ttl: Optional[int] = None
    ) -> None:
        """
        Cache price data for multiple tokens.
        
        Args:
            chain_id: Chain ID
            prices: Dictionary of price data by token address
            ttl: Time-to-live in seconds
        """
        for address, price_data in prices.items():
            await self.set(chain_id, address, price_data, ttl)
    
    async def clear(self) -> None:
        """Clear all cached data."""
        async with self._lock:
            self._cache.clear()
            logger.info("Price cache cleared")
    
    async def clear_expired(self) -> int:
        """
        Remove expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        async with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry["expires_at"] <= current_time
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.info(f"Removed {len(expired_keys)} expired entries from cache")
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        current_time = time.time()
        total_entries = len(self._cache)
        expired_entries = sum(
            1 for entry in self._cache.values()
            if entry["expires_at"] <= current_time
        )
        
        return {
            "total_entries": total_entries,
            "active_entries": total_entries - expired_entries,
            "expired_entries": expired_entries,
            "cache_size_bytes": self._estimate_size()
        }
    
    def _estimate_size(self) -> int:
        """Estimate cache size in bytes."""
        # Rough estimation - actual size may vary
        return len(str(self._cache).encode('utf-8'))


# Singleton instance with 60-second TTL for price data
price_cache = PriceCache(default_ttl=60)


class PriceCacheMiddleware:
    """Middleware for automatic cache management with 1inch service."""
    
    def __init__(self, cache: PriceCache):
        self.cache = cache
    
    async def get_token_prices_with_cache(
        self,
        oneinch_service,
        chain_id: int,
        token_addresses: List[str]
    ) -> Dict[str, Any]:
        """
        Get token prices with caching.
        
        Args:
            oneinch_service: OneInch service instance
            chain_id: Chain ID
            token_addresses: List of token addresses
            
        Returns:
            Dictionary of token prices
        """
        if not token_addresses:
            return {}
        
        # Normalize addresses
        normalized_addresses = [addr.lower() for addr in token_addresses]
        
        # Check cache first
        cached_prices = await self.cache.get_many(chain_id, normalized_addresses)
        
        # Find addresses not in cache
        missing_addresses = [
            addr for addr in normalized_addresses
            if addr not in cached_prices
        ]
        
        if missing_addresses:
            logger.info(
                f"Fetching {len(missing_addresses)} prices from API "
                f"({len(cached_prices)} found in cache)"
            )
            
            # Fetch missing prices from API
            fresh_prices = await oneinch_service._get_token_prices_direct(
                chain_id, missing_addresses
            )
            
            # Cache the fresh prices
            if fresh_prices:
                await self.cache.set_many(chain_id, fresh_prices)
                
                # Merge with cached prices
                cached_prices.update(fresh_prices)
        else:
            logger.info(f"All {len(cached_prices)} prices found in cache")
        
        return cached_prices


# Create middleware instance
price_cache_middleware = PriceCacheMiddleware(price_cache)


# Optional: Background task to clean up expired entries periodically
async def cleanup_expired_entries(interval: int = 300):
    """
    Background task to clean up expired cache entries.
    
    Args:
        interval: Cleanup interval in seconds (default: 5 minutes)
    """
    while True:
        try:
            await asyncio.sleep(interval)
            removed = await price_cache.clear_expired()
            if removed > 0:
                logger.info(f"Cache cleanup: removed {removed} expired entries")
        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")