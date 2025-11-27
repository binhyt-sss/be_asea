"""
Zone Management Endpoints
CRUD operations for working zones
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database.session import get_db
from schemas import database as schemas
from crud import zone_crud

router = APIRouter(prefix="/zones", tags=["Zones"])


@router.get("", response_model=List[schemas.WorkingZone])
async def get_all_zones(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db)
):
    """Get all zones with pagination"""
    zones = await zone_crud.get_all_zones(db, skip=skip, limit=limit)
    return zones


@router.get("/{zone_id}", response_model=schemas.WorkingZone)
async def get_zone(zone_id: str, db: AsyncSession = Depends(get_db)):
    """Get zone by ID"""
    zone = await zone_crud.get_zone_by_id(db, zone_id)
    if zone is None:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone


@router.post("", response_model=schemas.WorkingZone)
async def create_zone(
    zone_data: schemas.WorkingZoneCreate, 
    db: AsyncSession = Depends(get_db)
):
    """Create new zone"""
    existing_zone = await zone_crud.get_zone_by_id(db, zone_data.zone_id)
    if existing_zone:
        raise HTTPException(
            status_code=400, 
            detail=f"Zone with zone_id {zone_data.zone_id} already exists"
        )
    
    zone = await zone_crud.create_zone(db, zone_data)
    return zone
