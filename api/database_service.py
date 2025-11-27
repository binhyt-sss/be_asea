import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from loguru import logger

from database.session import get_db, init_db, close_db
from database import models as db_models
from schemas import database as schemas
from crud import user_crud, zone_crud
from utils.redis_cache import RedisCache
from config import get_settings

app = FastAPI(
    title="Database Service - Async", 
    version="2.0.0",
    description="Async SQLAlchemy + asyncpg with Dependency Injection"
)

settings = get_settings()
redis_cache = RedisCache(redis_config=settings.redis)


@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting Async Database Service...")
    await init_db()
    logger.info("✅ Database Service ready (Async + SQLAlchemy + asyncpg)")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Async Database Service...")
    await close_db()


@app.get("/health")
async def health_check():
    redis_stats = redis_cache.get_stats() if redis_cache.is_available() else {"enabled": False}
    return {
        "status": "healthy",
        "service": "database_async",
        "version": "2.0.0",
        "database": "PostgreSQL + asyncpg",
        "orm": "SQLAlchemy 2.0 async",
        "redis": redis_stats
    }


# ============================================================================
# USER ENDPOINTS
# ============================================================================

@app.get("/users", response_model=List[schemas.User])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all users with pagination"""
    try:
        users = await user_crud.get_all_users(db, skip=skip, limit=limit)
        return users
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{user_id}", response_model=schemas.User)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get user by ID"""
    try:
        user = await user_crud.get_user_by_id(db, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/global/{global_id}", response_model=schemas.User)
async def get_user_by_global_id(global_id: int, db: AsyncSession = Depends(get_db)):
    """Get user by global_id"""
    try:
        user = await user_crud.get_user_by_global_id(db, global_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user with global_id {global_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/users", response_model=schemas.User)
async def create_user(
    user_data: schemas.UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new user"""
    try:
        # Check if global_id already exists
        existing_user = await user_crud.get_user_by_global_id(db, user_data.global_id)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail=f"User with global_id {user_data.global_id} already exists"
            )

        user = await user_crud.create_user(db, user_data)
        
        # Invalidate Redis cache
        redis_cache.invalidate_users_dict()
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/users/{user_id}", response_model=schemas.User)
async def update_user(
    user_id: int,
    user_data: schemas.UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing user"""
    try:
        user = await user_crud.update_user(db, user_id, user_data)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Invalidate Redis cache
        redis_cache.invalidate_users_dict()
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/users/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a user"""
    try:
        success = await user_crud.delete_user(db, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Invalidate Redis cache
        redis_cache.invalidate_users_dict()
        
        return JSONResponse(content={
            "message": f"User {user_id} deleted successfully"
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users-dict")
async def get_users_dict(
    use_cache: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """Get users as dictionary mapping global_id to name"""
    try:
        # Try cache first
        if use_cache and redis_cache.is_available():
            cached_dict = redis_cache.get_users_dict()
            if cached_dict:
                logger.info(f"✅ Users dict from Redis cache ({len(cached_dict)} users)")
                return cached_dict

        # Get from database
        users_dict = await user_crud.get_users_dict(db)

        # Cache for future requests (1 hour TTL)
        if redis_cache.is_available():
            redis_cache.cache_users_dict(users_dict, ttl=3600)
            logger.info(f"✅ Cached users dict to Redis ({len(users_dict)} users)")

        return users_dict
    except Exception as e:
        logger.error(f"Error fetching users dict: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/by-zone/{zone_id}", response_model=List[schemas.User])
async def get_users_by_zone(zone_id: str, db: AsyncSession = Depends(get_db)):
    """Get all users in a specific zone"""
    try:
        users = await user_crud.get_users_by_zone(db, zone_id)
        return users
    except Exception as e:
        logger.error(f"Error fetching users for zone {zone_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WORKING ZONE ENDPOINTS
# ============================================================================

@app.get("/zones", response_model=List[schemas.WorkingZone])
async def get_all_zones(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all working zones with pagination"""
    try:
        zones = await zone_crud.get_all_zones(db, skip=skip, limit=limit)
        return zones
    except Exception as e:
        logger.error(f"Error fetching zones: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/zones/{zone_id}", response_model=schemas.WorkingZone)
async def get_zone(zone_id: str, db: AsyncSession = Depends(get_db)):
    """Get working zone by ID"""
    try:
        zone = await zone_crud.get_zone_by_id(db, zone_id)
        if zone is None:
            raise HTTPException(status_code=404, detail="Zone not found")
        return zone
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching zone {zone_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/zones/{zone_id}/with-users", response_model=schemas.WorkingZoneWithUsers)
async def get_zone_with_users(zone_id: str, db: AsyncSession = Depends(get_db)):
    """Get working zone with list of users"""
    try:
        zone = await zone_crud.get_zone_with_users(db, zone_id)
        if zone is None:
            raise HTTPException(status_code=404, detail="Zone not found")
        return zone
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching zone with users {zone_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/zones", response_model=schemas.WorkingZone)
async def create_zone(
    zone_data: schemas.WorkingZoneCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new working zone"""
    try:
        # Check if zone_id already exists
        existing_zone = await zone_crud.get_zone_by_id(db, zone_data.zone_id)
        if existing_zone:
            raise HTTPException(
                status_code=400,
                detail=f"Zone with zone_id {zone_data.zone_id} already exists"
            )

        zone = await zone_crud.create_zone(db, zone_data)
        return zone
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating zone: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/zones/{zone_id}", response_model=schemas.WorkingZone)
async def update_zone(
    zone_id: str,
    zone_data: schemas.WorkingZoneUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing working zone"""
    try:
        zone = await zone_crud.update_zone(db, zone_id, zone_data)
        if zone is None:
            raise HTTPException(status_code=404, detail="Zone not found")
        return zone
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating zone {zone_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/zones/{zone_id}")
async def delete_zone(zone_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a working zone"""
    try:
        success = await zone_crud.delete_zone(db, zone_id)
        if not success:
            raise HTTPException(status_code=404, detail="Zone not found")
        
        return JSONResponse(content={
            "message": f"Zone {zone_id} deleted successfully"
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting zone {zone_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STATISTICS ENDPOINTS
# ============================================================================

@app.get("/stats/users")
async def get_user_stats(db: AsyncSession = Depends(get_db)):
    """Get user statistics"""
    try:
        total_users = await user_crud.count_users(db)
        return {
            "total_users": total_users
        }
    except Exception as e:
        logger.error(f"Error fetching user stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats/zones")
async def get_zone_stats(db: AsyncSession = Depends(get_db)):
    """Get zone statistics with user counts"""
    try:
        total_zones = await zone_crud.count_zones(db)
        zones_with_counts = await zone_crud.get_zones_with_user_counts(db)
        
        return {
            "total_zones": total_zones,
            "zones": zones_with_counts
        }
    except Exception as e:
        logger.error(f"Error fetching zone stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# REDIS CACHE MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/cache/stats")
async def get_cache_stats():
    """Get Redis cache statistics"""
    return redis_cache.get_stats()


@app.post("/cache/invalidate/users-dict")
async def invalidate_users_cache():
    """Manually invalidate users dictionary cache"""
    try:
        success = redis_cache.invalidate_users_dict()
        if success:
            return {"message": "Users dict cache invalidated successfully"}
        else:
            return {"message": "Redis cache not available"}
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cache/clear")
async def clear_all_cache():
    """Clear all Redis cache keys (use with caution!)"""
    try:
        success = redis_cache.clear_all()
        if success:
            return {"message": "All cache cleared successfully"}
        else:
            return {"message": "Redis cache not available"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api.host, port=settings.api.database_api_port)


