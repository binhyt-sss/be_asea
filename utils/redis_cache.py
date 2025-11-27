"""
Redis Cache Manager for Backend API
Provides caching layer for database queries and session management
"""

import redis
import json
from typing import Dict, Optional, Any
from loguru import logger

# Import config - will be used if no config provided
try:
    from config import get_settings, RedisSettings
except ImportError:
    # Fallback for when config module doesn't exist yet
    RedisSettings = None
    get_settings = None


class RedisCache:
    """
    Redis cache manager for backend services

    Features:
    - Users dictionary caching (global_id -> name mapping)
    - Session data storage
    - Temporary data with TTL
    - Query result caching
    """

    def __init__(
        self,
        redis_config: Optional[Any] = None,  # RedisSettings or None
        host: str = None,
        port: int = None,
        db: int = None,
        enabled: bool = True
    ):
        """
        Initialize Redis Cache Manager

        Args:
            redis_config: Optional RedisSettings from config module (preferred)
            host: Redis server host (legacy, for backward compatibility)
            port: Redis server port (legacy, for backward compatibility)
            db: Redis database number (legacy, for backward compatibility)
            enabled: Enable/disable Redis caching (legacy, for backward compatibility)
        """
        # Use RedisSettings if provided
        if redis_config is not None:
            self.enabled = redis_config.enabled
            self.host = redis_config.host
            self.port = redis_config.port
            self.db = redis_config.db
        # Use individual parameters if provided (backward compatibility)
        elif host is not None or port is not None or db is not None:
            import os
            self.enabled = enabled and os.getenv('REDIS_ENABLE', 'true').lower() == 'true'
            self.host = host or os.getenv('REDIS_HOST', 'localhost')
            self.port = int(port or os.getenv('REDIS_PORT', 6379))
            self.db = int(db or os.getenv('REDIS_DB', 0))
        # Load from global settings
        elif get_settings is not None:
            settings = get_settings()
            redis_config = settings.redis
            self.enabled = redis_config.enabled
            self.host = redis_config.host
            self.port = redis_config.port
            self.db = redis_config.db
        else:
            # Fallback to environment variables (should not happen)
            import os
            self.enabled = enabled and os.getenv('REDIS_ENABLE', 'true').lower() == 'true'
            self.host = host or os.getenv('REDIS_HOST', 'localhost')
            self.port = int(port or os.getenv('REDIS_PORT', 6379))
            self.db = int(db or os.getenv('REDIS_DB', 0))

        try:
            self.redis = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True
            )
            # Test connection
            self.redis.ping()
            logger.info(f"✅ Redis cache connected: {self.host}:{self.port} (DB={self.db})")
        except redis.ConnectionError as e:
            logger.error(f"❌ Redis connection failed: {e}")
            logger.warning("⚠️  Running without Redis cache")
            self.enabled = False
            self.redis = None

    def is_available(self) -> bool:
        """Check if Redis is available"""
        return self.enabled and self.redis is not None

    # ========== Users Dictionary Caching ==========

    def cache_users_dict(self, users_dict: Dict[int, str], ttl: int = 3600) -> bool:
        """
        Cache users dictionary (global_id -> name mapping)

        Args:
            users_dict: Dictionary mapping global_id to person name
            ttl: Time-to-live in seconds (default: 3600s = 1 hour)

        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False

        try:
            key = "users:dict"
            # Convert int keys to strings for Redis
            data_to_store = {str(k): v for k, v in users_dict.items()}
            self.redis.hset(key, mapping=data_to_store)
            self.redis.expire(key, ttl)
            logger.info(f"✅ Cached {len(users_dict)} users (TTL={ttl}s)")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to cache users dict: {e}")
            return False

    def get_users_dict(self) -> Optional[Dict[int, str]]:
        """
        Get cached users dictionary

        Returns:
            Dictionary mapping global_id to person name, or None if not cached
        """
        if not self.is_available():
            return None

        try:
            key = "users:dict"
            data = self.redis.hgetall(key)
            if not data:
                return None
            # Convert string keys back to int
            return {int(k): v for k, v in data.items()}
        except Exception as e:
            logger.error(f"❌ Failed to get users dict from cache: {e}")
            return None

    def invalidate_users_dict(self) -> bool:
        """Invalidate cached users dictionary"""
        if not self.is_available():
            return False

        try:
            self.redis.delete("users:dict")
            logger.info("✅ Users dict cache invalidated")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to invalidate users dict: {e}")
            return False

    # ========== Generic Cache Operations ==========

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        Set a cache value with TTL

        Args:
            key: Cache key
            value: Value to cache (will be JSON-serialized if not string)
            ttl: Time-to-live in seconds (default: 300s = 5 min)

        Returns:
            True if successful
        """
        if not self.is_available():
            return False

        try:
            # Serialize non-string values
            if not isinstance(value, str):
                value = json.dumps(value)

            self.redis.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.error(f"❌ Failed to set cache key '{key}': {e}")
            return False

    def get(self, key: str, deserialize: bool = True) -> Optional[Any]:
        """
        Get a cache value

        Args:
            key: Cache key
            deserialize: Try to JSON-deserialize the value

        Returns:
            Cached value or None if not found
        """
        if not self.is_available():
            return None

        try:
            value = self.redis.get(key)
            if value is None:
                return None

            # Try to deserialize JSON
            if deserialize:
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value

            return value
        except Exception as e:
            logger.error(f"❌ Failed to get cache key '{key}': {e}")
            return None

    def delete(self, key: str) -> bool:
        """Delete a cache key"""
        if not self.is_available():
            return False

        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete cache key '{key}': {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if a key exists in cache"""
        if not self.is_available():
            return False

        try:
            return bool(self.redis.exists(key))
        except Exception as e:
            logger.error(f"❌ Failed to check cache key '{key}': {e}")
            return False

    # ========== Statistics ==========

    def get_stats(self) -> Dict:
        """
        Get Redis statistics

        Returns:
            Dictionary with stats
        """
        if not self.is_available():
            return {'enabled': False}

        try:
            info = self.redis.info()
            keys = self.redis.keys("*")
            return {
                'enabled': True,
                'host': self.host,
                'port': self.port,
                'db': self.db,
                'total_keys': len(keys),
                'memory_used': info.get('used_memory_human', 'N/A'),
                'connected_clients': info.get('connected_clients', 0),
                'uptime_seconds': info.get('uptime_in_seconds', 0)
            }
        except Exception as e:
            logger.error(f"❌ Failed to get Redis stats: {e}")
            return {'enabled': True, 'error': str(e)}

    def clear_all(self) -> bool:
        """
        Clear all keys (use with caution!)

        Returns:
            True if successful
        """
        if not self.is_available():
            return False

        try:
            keys = self.redis.keys("*")
            if keys:
                self.redis.delete(*keys)
            logger.info(f"✅ Cleared {len(keys)} keys from Redis")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to clear Redis: {e}")
            return False

