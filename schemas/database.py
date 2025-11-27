"""
Pydantic Schemas for API Request/Response DTOs
These are separate from SQLAlchemy models for clean separation of concerns
"""

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


# User Schemas

class UserBase(BaseModel):
    """Base user fields shared across schemas"""
    global_id: int = Field(..., description="Unique global identifier for the user")
    name: str = Field(..., min_length=1, max_length=100, description="User's name")


class UserCreate(UserBase):
    """Schema for creating a new user"""
    zone_ids: Optional[List[str]] = Field(default_factory=list, description="List of zone IDs to assign")


class UserUpdate(BaseModel):
    """Schema for updating user fields (all optional)"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    zone_ids: Optional[List[str]] = Field(None, description="List of zone IDs to assign (replaces existing)")


class User(UserBase):
    """Complete user schema for API responses"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserWithZones(User):
    """User with list of assigned zones (for relationship display)"""
    zones: List["WorkingZone"] = Field(default_factory=list, description="Zones assigned to this user")

    model_config = ConfigDict(from_attributes=True)


# Working Zone Schemas

class WorkingZoneBase(BaseModel):
    """Base zone fields shared across schemas"""
    zone_id: str = Field(..., description="Unique zone identifier")
    zone_name: str = Field(..., min_length=1, max_length=100, description="Zone name")
    x1: float = Field(..., description="Polygon point 1 - X coordinate")
    y1: float = Field(..., description="Polygon point 1 - Y coordinate")
    x2: float = Field(..., description="Polygon point 2 - X coordinate")
    y2: float = Field(..., description="Polygon point 2 - Y coordinate")
    x3: float = Field(..., description="Polygon point 3 - X coordinate")
    y3: float = Field(..., description="Polygon point 3 - Y coordinate")
    x4: float = Field(..., description="Polygon point 4 - X coordinate")
    y4: float = Field(..., description="Polygon point 4 - Y coordinate")


class WorkingZoneCreate(WorkingZoneBase):
    """Schema for creating a new working zone"""
    pass


class WorkingZoneUpdate(BaseModel):
    """Schema for updating zone fields (all optional)"""
    zone_name: Optional[str] = Field(None, min_length=1, max_length=100)
    x1: Optional[float] = None
    y1: Optional[float] = None
    x2: Optional[float] = None
    y2: Optional[float] = None
    x3: Optional[float] = None
    y3: Optional[float] = None
    x4: Optional[float] = None
    y4: Optional[float] = None


class WorkingZone(WorkingZoneBase):
    """Complete working zone schema for API responses"""
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class WorkingZoneWithUsers(WorkingZone):
    """Working zone with list of assigned users (for relationship display)"""
    users: List[User] = Field(default_factory=list, description="Users assigned to this zone")

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    'User',
    'UserCreate',
    'UserUpdate',
    'UserWithZones',
    'WorkingZone',
    'WorkingZoneCreate',
    'WorkingZoneUpdate',
    'WorkingZoneWithUsers'
]

