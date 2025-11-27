"""
SQLAlchemy ORM Models for Database Tables
Defines actual database table structures using SQLAlchemy async ORM
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func, Index
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from datetime import datetime
from typing import Optional, List


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    pass


class User(Base):
    """
    User table - Person ReID user information
    Relationship: Many-to-One with WorkingZone
    """
    __tablename__ = "user"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # User Data
    global_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    
    # Foreign Key to WorkingZone
    zone_id: Mapped[Optional[str]] = mapped_column(
        String, 
        ForeignKey("working_zone.zone_id", ondelete="SET NULL"), 
        nullable=True,
        index=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True
    )

    # Relationship
    zone: Mapped[Optional["WorkingZone"]] = relationship(
        "WorkingZone", 
        back_populates="users"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, global_id={self.global_id}, name='{self.name}', zone_id={self.zone_id})>"


class WorkingZone(Base):
    """
    Working Zone table - Polygon coordinates for zones
    Relationship: One-to-Many with User
    """
    __tablename__ = "working_zone"

    # Primary Key
    zone_id: Mapped[str] = mapped_column(String, primary_key=True)
    
    # Zone Data
    zone_name: Mapped[str] = mapped_column(String, nullable=False)
    
    # Polygon Coordinates (4 points: x1,y1 to x4,y4)
    x1: Mapped[float] = mapped_column(Float, nullable=False)
    y1: Mapped[float] = mapped_column(Float, nullable=False)
    x2: Mapped[float] = mapped_column(Float, nullable=False)
    y2: Mapped[float] = mapped_column(Float, nullable=False)
    x3: Mapped[float] = mapped_column(Float, nullable=False)
    y3: Mapped[float] = mapped_column(Float, nullable=False)
    x4: Mapped[float] = mapped_column(Float, nullable=False)
    y4: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True
    )

    # Relationship
    users: Mapped[List["User"]] = relationship(
        "User", 
        back_populates="zone",
        cascade="all, delete-orphan"  # Delete users when zone is deleted
    )

    def __repr__(self) -> str:
        return f"<WorkingZone(zone_id='{self.zone_id}', zone_name='{self.zone_name}', users_count={len(self.users)})>"


# Indexes for performance
Index("idx_user_global_id", User.global_id)
Index("idx_user_zone_id", User.zone_id)



