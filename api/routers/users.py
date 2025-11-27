"""
User Management Endpoints
CRUD operations for users with Redis cache invalidation
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel

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


@router.get("/{user_id}/zones", response_model=schemas.UserWithZones)
async def get_user_with_zones(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get user with all assigned zones"""
    user = await user_crud.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


class UserZonesUpdate(BaseModel):
    """Schema for updating user's zone assignments"""
    zone_ids: List[str]


@router.post("/{user_id}/zones/assign")
async def assign_zones_to_user(
    user_id: int,
    zones_data: UserZonesUpdate,
    db: AsyncSession = Depends(get_db),
    redis_cache = Depends(get_redis_cache)
):
    """Assign multiple zones to a user (replaces existing assignments)"""
    update_data = schemas.UserUpdate(zone_ids=zones_data.zone_ids)
    user = await user_crud.update_user(db, user_id, update_data)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    await redis_cache.invalidate_users_dict()
    return {"message": f"Assigned {len(zones_data.zone_ids)} zones to user {user_id}", "zones": zones_data.zone_ids}


@router.post("/{user_id}/zones/{zone_id}/add")
async def add_zone_to_user(
    user_id: int,
    zone_id: str,
    db: AsyncSession = Depends(get_db),
    redis_cache = Depends(get_redis_cache)
):
    """Add a single zone to user's existing zones"""
    user = await user_crud.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get existing zone IDs
    existing_zone_ids = [z.zone_id for z in user.zones]
    if zone_id in existing_zone_ids:
        return {"message": f"User {user_id} already has zone {zone_id}", "zones": existing_zone_ids}
    
    # Add new zone
    new_zone_ids = existing_zone_ids + [zone_id]
    update_data = schemas.UserUpdate(zone_ids=new_zone_ids)
    user = await user_crud.update_user(db, user_id, update_data)
    await redis_cache.invalidate_users_dict()
    return {"message": f"Added zone {zone_id} to user {user_id}", "zones": new_zone_ids}


@router.delete("/{user_id}/zones/{zone_id}")
async def remove_zone_from_user(
    user_id: int,
    zone_id: str,
    db: AsyncSession = Depends(get_db),
    redis_cache = Depends(get_redis_cache)
):
    """Remove a single zone from user's assignments"""
    user = await user_crud.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get existing zone IDs
    existing_zone_ids = [z.zone_id for z in user.zones]
    if zone_id not in existing_zone_ids:
        return {"message": f"User {user_id} doesn't have zone {zone_id}", "zones": existing_zone_ids}
    
    # Remove zone
    new_zone_ids = [zid for zid in existing_zone_ids if zid != zone_id]
    update_data = schemas.UserUpdate(zone_ids=new_zone_ids)
    user = await user_crud.update_user(db, user_id, update_data)
    await redis_cache.invalidate_users_dict()
    return {"message": f"Removed zone {zone_id} from user {user_id}", "zones": new_zone_ids}
