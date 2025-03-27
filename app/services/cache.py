import json
import redis.asyncio as redis
from app.core.config import settings
import asyncio

class RedisCache:
    _instance = None
    _redis = None
    
    @classmethod
    async def get_instance(cls):
        """
        Get singleton instance of RedisCache.
        Initializes the connection if needed.
        """
        if cls._instance is None:
            cls._instance = RedisCache()
            await cls._instance._init_redis()
        return cls._instance
    
    @classmethod
    async def __call__(cls):
        instance = await cls.get_instance()
        return instance
    
    async def _init_redis(self):
        """Initialize the Redis connection"""
        try:
            self._redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                decode_responses=True,
                socket_timeout=1.0,  # Add timeout to prevent hanging
                socket_connect_timeout=1.0,
                health_check_interval=30
            )
            # Test connection
            await self._redis.ping()
        except Exception as e:
            print(f"Error connecting to Redis: {e}")
            # Don't raise - continue without cache if Redis is unavailable
            self._redis = None
    
    def _get_cache_key(self, netuid, hotkey):
        """Generate a cache key for the dividends query"""
        return f"tao_dividends:{netuid}:{hotkey}"
    
    async def get(self, key):
        """
        Get a value from cache by key with timeout protection
        """
        if self._redis is None:
            return None
        
        try:
            # Add timeout to prevent hanging on Redis operations
            cached_data = await asyncio.wait_for(self._redis.get(key), timeout=0.5)
            
            if cached_data:
                return json.loads(cached_data)
            return None
        except asyncio.TimeoutError:
            print("Redis get operation timed out")
            return None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    async def set(self, key, value, ttl=None):
        """
        Set a value in cache with timeout protection
        """
        if self._redis is None:
            return False
        
        if ttl is None:
            ttl = settings.CACHE_TTL
            
        try:
            # Add timeout to prevent hanging on Redis operations
            await asyncio.wait_for(
                self._redis.setex(key, ttl, json.dumps(value)),
                timeout=0.5
            )
            return True
        except asyncio.TimeoutError:
            print("Redis set operation timed out")
            return False
        except Exception as e:
            print(f"Redis set error: {e}")
            return False
    
    async def get_cached_dividends(self, netuid, hotkey):
        """
        Get cached dividend data if available
        
        Args:
            netuid: The subnet ID
            hotkey: The account ID
            
        Returns:
            dict or None: Cached data if found, None otherwise
        """
        if self._redis is None:
            await self._init_redis()
        
        key = self._get_cache_key(netuid, hotkey)
        cached_data = await self.get(key)
        
        if cached_data:
            return cached_data
        return None
    
    async def cache_dividends(self, netuid, hotkey, data):
        """
        Cache dividend data with TTL
        
        Args:
            netuid: The subnet ID
            hotkey: The account ID
            data: The data to cache
        """
        if self._redis is None:
            await self._init_redis()
        
        key = self._get_cache_key(netuid, hotkey)
        return await self.set(key, data, settings.CACHE_TTL)