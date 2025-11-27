"""
User CRUD operations using async SQLAlchemy
Repository pattern for clean separation of data access logic
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from sqlalchemy.orm import selectinload
from typing import List, Optional

from database.models import User, WorkingZone
from schemas import database as schemas


async def get_all_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
    """
    Get all users with pagination
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of User objects
    """
    result = await db.execute(
        select(User)
        .options(selectinload(User.zone))  # Eager load zone relationship
        .order_by(User.global_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """
    Get user by primary key ID
    
    Args:
        db: Database session
        user_id: User's primary key
        
    Returns:
        User object or None if not found
    """
    result = await db.execute(
        select(User)
        .options(selectinload(User.zone))
        .where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_global_id(db: AsyncSession, global_id: int) -> Optional[User]:
    """
    Get user by global_id (unique business key)
    
    Args:
        db: Database session
        global_id: User's global identifier
        
    Returns:
        User object or None if not found
    """
    result = await db.execute(
        select(User)
        .options(selectinload(User.zone))
        .where(User.global_id == global_id)
    )
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_in: schemas.UserCreate) -> User:
    """
    Create a new user
    
    Args:
        db: Database session
        user_in: User creation schema
        
    Returns:
        Created User object
    """
    db_user = User(
        global_id=user_in.global_id,
        name=user_in.name,
        zone_id=user_in.zone_id
    )
    db.add(db_user)
    await db.flush()  # Flush to get ID without committing
    await db.refresh(db_user)  # Refresh to load defaults and relationships
    return db_user


async def update_user(db: AsyncSession, user_id: int, user_in: schemas.UserUpdate) -> Optional[User]:
    """
    Update existing user
    
    Args:
        db: Database session
        user_id: User's primary key
        user_in: User update schema
        
    Returns:
        Updated User object or None if not found
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    
    # Update only provided fields
    update_data = user_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.flush()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user_id: int) -> bool:
    """
    Delete user by ID
    
    Args:
        db: Database session
        user_id: User's primary key
        
    Returns:
        True if deleted, False if not found
    """
    result = await db.execute(
        delete(User).where(User.id == user_id)
    )
    await db.flush()
    return result.rowcount > 0


async def get_users_by_zone(db: AsyncSession, zone_id: str) -> List[User]:
    """
    Get all users assigned to a specific zone
    
    Args:
        db: Database session
        zone_id: Zone identifier
        
    Returns:
        List of User objects in the zone
    """
    result = await db.execute(
        select(User)
        .where(User.zone_id == zone_id)
        .order_by(User.global_id)
    )
    return result.scalars().all()


async def count_users(db: AsyncSession) -> int:
    """
    Get total count of users
    
    Args:
        db: Database session
        
    Returns:
        Total number of users
    """
    result = await db.execute(select(func.count()).select_from(User))
    return result.scalar_one()


async def get_users_dict(db: AsyncSession) -> dict:
    """
    Get all users as dictionary {global_id: name}
    Useful for caching and quick lookups
    
    Args:
        db: Database session
        
    Returns:
        Dictionary mapping global_id to user name
    """
    result = await db.execute(
        select(User.global_id, User.name).order_by(User.global_id)
    )
    return {global_id: name for global_id, name in result.all()}
