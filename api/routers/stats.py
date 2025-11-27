"""
Statistics Endpoints
Aggregate statistics for users and zones
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_db
from crud import user_crud, zone_crud

router = APIRouter(prefix="/stats", tags=["Statistics"])


@router.get("/users")
async def get_user_stats(db: AsyncSession = Depends(get_db)):
    """Get user statistics"""
    total_users = await user_crud.count_users(db)
    return {"total_users": total_users}


@router.get("/zones")
async def get_zone_stats(db: AsyncSession = Depends(get_db)):
    """Get zone statistics with user counts"""
    total_zones = await zone_crud.count_zones(db)
    zones_with_counts = await zone_crud.get_zones_with_user_counts(db)
    return {"total_zones": total_zones, "zones": zones_with_counts}
