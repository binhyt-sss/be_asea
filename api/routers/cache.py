"""
Cache Management Endpoints
Redis cache statistics and invalidation
"""

from fastapi import APIRouter, Depends

from api.dependencies import get_redis_cache

router = APIRouter(prefix="/cache", tags=["Cache"])


@router.get("/stats")
async def get_cache_stats(redis_cache = Depends(get_redis_cache)):
    """Get Redis cache statistics"""
    return await redis_cache.get_stats()


@router.post("/invalidate/users-dict")
async def invalidate_users_cache(redis_cache = Depends(get_redis_cache)):
    """Invalidate users dictionary cache"""
    success = await redis_cache.invalidate_users_dict()
    return {
        "message": "Users dict cache invalidated" if success else "Redis not available"
    }
