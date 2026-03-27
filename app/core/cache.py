"""
Simple in-memory cache for the application.
Replaces Redis with a lightweight Python dictionary.
"""
from datetime import datetime, timedelta
from typing import Any, Optional, Dict
import json
import asyncio
from collections import defaultdict

class InMemoryCache:
    """Thread-safe in-memory cache with TTL support"""
    
    def __init__(self):
        self._cache: Dict[str, str] = {}
        self._expiry: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache if not expired"""
        async with self._lock:
            if key in self._cache:
                if datetime.now() < self._expiry.get(key, datetime.min):
                    return self._cache[key]
                else:
                    # Expired, remove it
                    await self._delete_unsafe(key)
            return None
    
    async def set(self, key: str, value: str):
        """Set value without expiration"""
        async with self._lock:
            self._cache[key] = value
    
    async def setex(self, key: str, ttl: int, value: str):
        """Set value with TTL in seconds"""
        async with self._lock:
            self._cache[key] = value
            self._expiry[key] = datetime.now() + timedelta(seconds=ttl)
    
    async def delete(self, key: str):
        """Delete a key from cache"""
        async with self._lock:
            await self._delete_unsafe(key)
    
    async def _delete_unsafe(self, key: str):
        """Delete without lock (internal use)"""
        self._cache.pop(key, None)
        self._expiry.pop(key, None)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists and is not expired"""
        value = await self.get(key)
        return value is not None
    
    async def incr(self, key: str) -> int:
        """Increment integer value"""
        async with self._lock:
            current = self._cache.get(key, "0")
            new_value = int(current) + 1
            self._cache[key] = str(new_value)
            return new_value
    
    async def expire(self, key: str, ttl: int):
        """Set expiration on existing key"""
        async with self._lock:
            if key in self._cache:
                self._expiry[key] = datetime.now() + timedelta(seconds=ttl)
    
    async def keys(self, pattern: str = "*") -> list:
        """Get all keys matching pattern (simple * wildcard support)"""
        async with self._lock:
            if pattern == "*":
                return list(self._cache.keys())
            
            # Simple wildcard support
            if "*" in pattern:
                prefix = pattern.split("*")[0]
                return [k for k in self._cache.keys() if k.startswith(prefix)]
            
            return [pattern] if pattern in self._cache else []
    
    async def clear(self):
        """Clear all cache"""
        async with self._lock:
            self._cache.clear()
            self._expiry.clear()
    
    def __len__(self):
        """Get cache size"""
        return len(self._cache)


# Global cache instance
cache = InMemoryCache()
