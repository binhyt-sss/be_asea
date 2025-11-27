"""
Quick test to verify Async Redis operations
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from utils.redis_cache import RedisCache
from config import get_settings
from loguru import logger

async def test_async_redis():
    logger.info("🧪 Testing Async Redis operations...")
    
    settings = get_settings()
    redis_cache = RedisCache(redis_config=settings.redis)
    
    try:
        # Test 1: Cache users dict
        logger.info("\n1️⃣ Testing cache_users_dict...")
        test_data = {1001: "User A", 1002: "User B", 1003: "User C"}
        result = await redis_cache.cache_users_dict(test_data, ttl=60)
        logger.info(f"   Cache result: {result}")
        
        # Test 2: Get users dict
        logger.info("\n2️⃣ Testing get_users_dict...")
        cached = await redis_cache.get_users_dict()
        logger.info(f"   Retrieved: {cached}")
        assert cached == test_data, "Data mismatch!"
        
        # Test 3: Get stats
        logger.info("\n3️⃣ Testing get_stats...")
        stats = await redis_cache.get_stats()
        logger.info(f"   Stats: {stats}")
        
        # Test 4: Invalidate cache
        logger.info("\n4️⃣ Testing invalidate_users_dict...")
        result = await redis_cache.invalidate_users_dict()
        logger.info(f"   Invalidate result: {result}")
        
        # Test 5: Verify cache cleared
        logger.info("\n5️⃣ Verifying cache cleared...")
        cached = await redis_cache.get_users_dict()
        logger.info(f"   After invalidate: {cached}")
        assert cached is None, "Cache not cleared!"
        
        # Test 6: Generic set/get
        logger.info("\n6️⃣ Testing generic set/get...")
        await redis_cache.set("test:key", {"nested": "value"}, ttl=30)
        value = await redis_cache.get("test:key")
        logger.info(f"   Retrieved: {value}")
        
        logger.info("\n✅ All async Redis tests passed!")
        
    finally:
        await redis_cache.close()

if __name__ == "__main__":
    asyncio.run(test_async_redis())
