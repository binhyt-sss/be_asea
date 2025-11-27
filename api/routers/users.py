"""
User Management Endpoints
CRUD operations for users with Redis cache invalidation
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database.session import get_db
from schemas import database as schemas
from crud import user_crud
from api.dependencies import get_redis_cache

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=List[schemas.User])
async def get_all_users(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db)
):
    """Get all users with pagination"""
    users = await user_crud.get_all_users(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=schemas.User)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get user by ID"""
    user = await user_crud.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("", response_model=schemas.User)
async def create_user(
    user_data: schemas.UserCreate, 
    db: AsyncSession = Depends(get_db),
    redis_cache = Depends(get_redis_cache)
):
    """Create new user"""
    existing_user = await user_crud.get_user_by_global_id(db, user_data.global_id)
    if existing_user:
        raise HTTPException(
            status_code=400, 
            detail=f"User with global_id {user_data.global_id} already exists"
        )
    
    user = await user_crud.create_user(db, user_data)
    await redis_cache.invalidate_users_dict()
    return user


@router.put("/{user_id}", response_model=schemas.User)
async def update_user(
    user_id: int, 
    user_data: schemas.UserUpdate, 
    db: AsyncSession = Depends(get_db),
    redis_cache = Depends(get_redis_cache)
):
    """Update user"""
    user = await user_crud.update_user(db, user_id, user_data)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    await redis_cache.invalidate_users_dict()
    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int, 
    db: AsyncSession = Depends(get_db),
    redis_cache = Depends(get_redis_cache)
):
    """Delete user"""
    success = await user_crud.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    await redis_cache.invalidate_users_dict()
    return JSONResponse(content={"message": f"User {user_id} deleted successfully"})


@router.get("-dict", name="get_users_dict")
async def get_users_dict(
    use_cache: bool = True,
    db: AsyncSession = Depends(get_db),
    redis_cache = Depends(get_redis_cache)
):
    """Get users dictionary (cached)"""
    if use_cache and redis_cache.is_available():
        cached_dict = await redis_cache.get_users_dict()
        if cached_dict:
            return cached_dict
    
    users_dict = await user_crud.get_users_dict(db)
    if redis_cache.is_available():
        await redis_cache.cache_users_dict(users_dict, ttl=3600)
    return users_dict


@router.get("/by-zone/{zone_id}", response_model=List[schemas.User])
async def get_users_by_zone(
    zone_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all users in a specific zone"""
    users = await user_crud.get_users_by_zone(db, zone_id)
    return users
