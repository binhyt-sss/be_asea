"""
SQLAlchemy ORM Models for Database Tables
Defines actual database table structures using SQLAlchemy async ORM
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func, Index, Table
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from datetime import datetime
from typing import Optional, List


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    pass


# Association table for Many-to-Many relationship between User and WorkingZone
user_zone_association = Table(
    "user_zone_association",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("user.id", ondelete="CASCADE"), primary_key=True),
    Column("zone_id", String, ForeignKey("working_zone.zone_id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False)
)


class User(Base):
    """
    User table - Person ReID user information
    Relationship: Many-to-Many with WorkingZone
    """
    __tablename__ = "user"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # User Data
    global_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    
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

    # Many-to-Many Relationship with WorkingZone
    zones: Mapped[List["WorkingZone"]] = relationship(
        "WorkingZone",
        secondary=user_zone_association,
        back_populates="users",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, global_id={self.global_id}, name='{self.name}', zones_count={len(self.zones)})>"


class WorkingZone(Base):
    """
    Working Zone table - Polygon coordinates for zones
    Relationship: Many-to-Many with User
    """
    __tablename__ = "working_zone"

    # Primary Key
    zone_id: Mapped[str] = mapped_column(String, primary_key=True)

    # Zone Data
    zone_name: Mapped[str] = mapped_column(String, nullable=False)

    # Violation threshold in seconds (zone-specific config)
    violation_threshold: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

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

    # Many-to-Many Relationship with User
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_zone_association,
        back_populates="zones",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<WorkingZone(zone_id='{self.zone_id}', zone_name='{self.zone_name}', users_count={len(self.users)})>"


class ViolationLog(Base):
    """
    Violation Log table - Track violation history
    Records when users exceed violation threshold in zones
    """
    __tablename__ = "violation_logs"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Keys
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    zone_id: Mapped[str] = mapped_column(String, nullable=False, index=True)

    # Violation Data
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration: Mapped[float] = mapped_column(Float, nullable=False)  # in seconds
    threshold: Mapped[int] = mapped_column(Integer, nullable=False)  # threshold at time of violation

    # Additional Context (optional)
    user_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    zone_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<ViolationLog(id={self.id}, user_id='{self.user_id}', zone_id='{self.zone_id}', duration={self.duration}s)>"


# Indexes for performance
Index("idx_user_global_id", User.global_id)
Index("idx_violation_user_id", ViolationLog.user_id)
Index("idx_violation_zone_id", ViolationLog.zone_id)
Index("idx_violation_start_time", ViolationLog.start_time)



