"""
Working Zone CRUD operations using async SQLAlchemy
Repository pattern for zone management
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from sqlalchemy.orm import selectinload
from typing import List, Optional

from database.models import WorkingZone, User, user_zone_association
from schemas import database as schemas


async def get_all_zones(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[WorkingZone]:
    """
    Get all working zones with pagination
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of WorkingZone objects
    """
    result = await db.execute(
        select(WorkingZone)
        .order_by(WorkingZone.zone_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def get_zone_by_id(db: AsyncSession, zone_id: str) -> Optional[WorkingZone]:
    """
    Get working zone by ID
    
    Args:
        db: Database session
        zone_id: Zone identifier (primary key)
        
    Returns:
        WorkingZone object or None if not found
    """
    result = await db.execute(
        select(WorkingZone).where(WorkingZone.zone_id == zone_id)
    )
    return result.scalar_one_or_none()


async def get_zone_with_users(db: AsyncSession, zone_id: str) -> Optional[WorkingZone]:
    """
    Get working zone with all assigned users (eager loading)
    
    Args:
        db: Database session
        zone_id: Zone identifier
        
    Returns:
        WorkingZone object with users loaded, or None if not found
    """
    result = await db.execute(
        select(WorkingZone)
        .options(selectinload(WorkingZone.users))  # Eager load users
        .where(WorkingZone.zone_id == zone_id)
    )
    return result.scalar_one_or_none()


async def create_zone(db: AsyncSession, zone_in: schemas.WorkingZoneCreate) -> WorkingZone:
    """
    Create a new working zone
    
    Args:
        db: Database session
        zone_in: Zone creation schema
        
    Returns:
        Created WorkingZone object
    """
    db_zone = WorkingZone(
        zone_id=zone_in.zone_id,
        zone_name=zone_in.zone_name,
        x1=zone_in.x1,
        y1=zone_in.y1,
        x2=zone_in.x2,
        y2=zone_in.y2,
        x3=zone_in.x3,
        y3=zone_in.y3,
        x4=zone_in.x4,
        y4=zone_in.y4
    )
    db.add(db_zone)
    await db.flush()
    await db.refresh(db_zone)
    return db_zone


async def update_zone(db: AsyncSession, zone_id: str, zone_in: schemas.WorkingZoneUpdate) -> Optional[WorkingZone]:
    """
    Update existing working zone
    
    Args:
        db: Database session
        zone_id: Zone identifier
        zone_in: Zone update schema
        
    Returns:
        Updated WorkingZone object or None if not found
    """
    zone = await get_zone_by_id(db, zone_id)
    if not zone:
        return None
    
    # Update only provided fields
    update_data = zone_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(zone, field, value)
    
    await db.flush()
    await db.refresh(zone)
    return zone


async def delete_zone(db: AsyncSession, zone_id: str) -> bool:
    """
    Delete working zone by ID
    
    Args:
        db: Database session
        zone_id: Zone identifier
        
    Returns:
        True if deleted, False if not found
        
    Note:
        Due to cascade="all, delete-orphan", all users in this zone
        will also be deleted. Consider setting zone_id to NULL instead.
    """
    result = await db.execute(
        delete(WorkingZone).where(WorkingZone.zone_id == zone_id)
    )
    await db.flush()
    return result.rowcount > 0


async def count_zones(db: AsyncSession) -> int:
    """
    Get total count of working zones
    
    Args:
        db: Database session
        
    Returns:
        Total number of zones
    """
    result = await db.execute(select(func.count()).select_from(WorkingZone))
    return result.scalar_one()


async def get_zones_with_user_counts(db: AsyncSession) -> List[dict]:
    """
    Get all zones with user count for each
    
    Args:
        db: Database session
        
    Returns:
        List of dicts with zone info and user_count
    """
    result = await db.execute(
        select(
            WorkingZone.zone_id,
            WorkingZone.zone_name,
            func.count(user_zone_association.c.user_id).label('user_count')
        )
        .select_from(WorkingZone)
        .outerjoin(user_zone_association, WorkingZone.zone_id == user_zone_association.c.zone_id)
        .group_by(WorkingZone.zone_id, WorkingZone.zone_name)
        .order_by(WorkingZone.zone_id)
    )
    
    return [
        {
            'zone_id': zone_id,
            'zone_name': zone_name,
            'user_count': user_count
        }
        for zone_id, zone_name, user_count in result.all()
    ]
