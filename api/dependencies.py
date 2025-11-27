"""
FastAPI Dependencies
Shared dependencies for dependency injection
"""

from collections import deque
from utils.redis_cache import RedisCache
from config import get_settings

# Global instances
_redis_cache = None
_message_buffer = deque(maxlen=100)


def get_redis_cache() -> RedisCache:
    """Dependency to get Redis cache instance"""
    global _redis_cache
    if _redis_cache is None:
        settings = get_settings()
        _redis_cache = RedisCache(redis_config=settings.redis)
    return _redis_cache


def get_message_buffer() -> deque:
    """Dependency to get Kafka message buffer"""
    return _message_buffer
