"""
Violations Management API
Manual review and processing of violations
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from loguru import logger
from sqlalchemy import select, desc, func

from api.services.message_processor import MessageProcessor
from database.session import async_session_maker
from database.models import ViolationLog


router = APIRouter(
    prefix="/violations",
    tags=["violations"]
)


# ================================================================
# Request/Response Models
# ================================================================

class ViolationApprovalRequest(BaseModel):
    """Request model for approving/rejecting violations"""
    action: str  # 'approve' or 'reject'

    class Config:
        json_schema_extra = {
            "example": {
                "action": "approve"
            }
        }


class ViolationResponse(BaseModel):
    """Response model for violation"""
    user_id: str
    user_name: str
    zone_id: str
    zone_name: str
    status: str
    timestamp: float
    severity: str | None = None
    iop: float | None = None
    threshold: float | None = None


class ViolationsQueueResponse(BaseModel):
    """Response model for violations queue"""
    count: int
    violations: List[Dict[Any, Any]]


class StatisticsResponse(BaseModel):
    """Response model for statistics"""
    pending_violations: int
    queue_capacity: int


class ActionResponse(BaseModel):
    """Response model for actions"""
    success: bool
    message: str


# ================================================================
# Endpoints
# ================================================================

@router.get(
    "/queue",
    response_model=ViolationsQueueResponse,
    summary="Get violations queue",
    description="Get all violations waiting for manual review"
)
async def get_violations_queue():
    """
    Get violations queue

    Returns all violations that are waiting for manual review.
    These violations have been auto-detected but require manual approval.
    """
    try:
        violations = MessageProcessor.get_violations_queue()

        return ViolationsQueueResponse(
            count=len(violations),
            violations=violations
        )

    except Exception as e:
        logger.error(f"Error getting violations queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{violation_id}/approve",
    response_model=ActionResponse,
    summary="Approve violation",
    description="Approve a violation for advanced processing (save full details, send alerts)"
)
async def approve_violation(violation_id: str):
    """
    Approve violation

    Args:
        violation_id: User ID from the violation to approve

    This will:
    - Save full violation details to database
    - Send detailed alerts (Telegram, Email, etc.)
    - Remove from queue
    """
    try:
        success = await MessageProcessor.manual_approve_violation(
            violation_id=violation_id,
            action='approve'
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Violation not found: {violation_id}"
            )

        return ActionResponse(
            success=True,
            message=f"Violation {violation_id} approved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving violation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{violation_id}/reject",
    response_model=ActionResponse,
    summary="Reject violation",
    description="Reject a violation (mark as false positive)"
)
async def reject_violation(violation_id: str):
    """
    Reject violation

    Args:
        violation_id: User ID from the violation to reject

    This will mark the violation as a false positive and remove it from the queue.
    """
    try:
        success = await MessageProcessor.manual_approve_violation(
            violation_id=violation_id,
            action='reject'
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Violation not found: {violation_id}"
            )

        return ActionResponse(
            success=True,
            message=f"Violation {violation_id} rejected successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting violation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{violation_id}",
    response_model=ActionResponse,
    summary="Process violation with action",
    description="Process a violation with specified action (approve/reject)"
)
async def process_violation(violation_id: str, request: ViolationApprovalRequest):
    """
    Process violation with action

    Args:
        violation_id: User ID from the violation
        request: Action to perform (approve/reject)

    This is an alternative endpoint that accepts action in the request body.
    """
    try:
        if request.action not in ['approve', 'reject']:
            raise HTTPException(
                status_code=400,
                detail="Action must be 'approve' or 'reject'"
            )

        success = await MessageProcessor.manual_approve_violation(
            violation_id=violation_id,
            action=request.action
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Violation not found: {violation_id}"
            )

        return ActionResponse(
            success=True,
            message=f"Violation {violation_id} {request.action}d successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing violation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/statistics",
    response_model=StatisticsResponse,
    summary="Get processing statistics",
    description="Get statistics about violation processing"
)
async def get_statistics():
    """
    Get statistics

    Returns statistics about the violation processing system:
    - Number of pending violations
    - Queue capacity
    """
    try:
        stats = MessageProcessor.get_statistics()

        return StatisticsResponse(
            pending_violations=stats.get('pending_violations', 0),
            queue_capacity=stats.get('queue_capacity', 100)
        )

    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ================================================================
# Database Violation Logs Endpoints
# ================================================================

@router.get(
    "/logs",
    summary="Get violation logs from database",
    description="Get violation history from database with pagination and filters"
)
async def get_violation_logs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of records to return"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    zone_id: Optional[str] = Query(None, description="Filter by zone ID"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date")
):
    """
    Get violation logs with optional filtering

    Returns violation history from PostgreSQL database.
    Supports pagination and filtering by user, zone, and date range.
    """
    try:
        async with async_session_maker() as session:
            # Base query
            stmt = select(ViolationLog)

            # Apply filters
            if user_id:
                stmt = stmt.where(ViolationLog.user_id == user_id)
            if zone_id:
                stmt = stmt.where(ViolationLog.zone_id == zone_id)
            if start_date:
                stmt = stmt.where(ViolationLog.start_time >= start_date)
            if end_date:
                stmt = stmt.where(ViolationLog.start_time <= end_date)

            # Order by most recent first
            stmt = stmt.order_by(desc(ViolationLog.created_at))

            # Count total
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total_result = await session.execute(count_stmt)
            total = total_result.scalar()

            # Apply pagination
            stmt = stmt.offset(skip).limit(limit)

            # Execute query
            result = await session.execute(stmt)
            violations = result.scalars().all()

            # Convert to dict
            violations_data = [
                {
                    "id": v.id,
                    "user_id": v.user_id,
                    "zone_id": v.zone_id,
                    "user_name": v.user_name,
                    "zone_name": v.zone_name,
                    "start_time": v.start_time.isoformat() if v.start_time else None,
                    "end_time": v.end_time.isoformat() if v.end_time else None,
                    "duration": v.duration,
                    "threshold": v.threshold,
                    "created_at": v.created_at.isoformat() if v.created_at else None
                }
                for v in violations
            ]

            return {
                "total": total,
                "skip": skip,
                "limit": limit,
                "count": len(violations_data),
                "violations": violations_data
            }

    except Exception as e:
        logger.error(f"Error getting violation logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/logs/{violation_id}",
    summary="Get specific violation log",
    description="Get detailed information about a specific violation"
)
async def get_violation_log(violation_id: int):
    """
    Get violation log by ID

    Args:
        violation_id: Violation log ID

    Returns:
        Detailed violation information
    """
    try:
        async with async_session_maker() as session:
            stmt = select(ViolationLog).where(ViolationLog.id == violation_id)
            result = await session.execute(stmt)
            violation = result.scalar_one_or_none()

            if not violation:
                raise HTTPException(
                    status_code=404,
                    detail=f"Violation log not found: {violation_id}"
                )

            return {
                "id": violation.id,
                "user_id": violation.user_id,
                "zone_id": violation.zone_id,
                "user_name": violation.user_name,
                "zone_name": violation.zone_name,
                "start_time": violation.start_time.isoformat() if violation.start_time else None,
                "end_time": violation.end_time.isoformat() if violation.end_time else None,
                "duration": violation.duration,
                "threshold": violation.threshold,
                "created_at": violation.created_at.isoformat() if violation.created_at else None
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting violation log: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/logs/stats/summary",
    summary="Get violation summary statistics",
    description="Get aggregated statistics about violations"
)
async def get_violation_summary():
    """
    Get violation summary statistics

    Returns:
        - Total violations
        - Violations by user
        - Violations by zone
        - Average duration
        - Recent trends
    """
    try:
        async with async_session_maker() as session:
            # Total violations
            total_stmt = select(func.count(ViolationLog.id))
            total_result = await session.execute(total_stmt)
            total_violations = total_result.scalar() or 0

            # Average duration
            avg_stmt = select(func.avg(ViolationLog.duration))
            avg_result = await session.execute(avg_stmt)
            avg_duration = avg_result.scalar() or 0

            # Top violating users
            top_users_stmt = (
                select(
                    ViolationLog.user_name,
                    func.count(ViolationLog.id).label('count')
                )
                .group_by(ViolationLog.user_name)
                .order_by(desc('count'))
                .limit(10)
            )
            top_users_result = await session.execute(top_users_stmt)
            top_users = [
                {"user_name": row[0], "violation_count": row[1]}
                for row in top_users_result
            ]

            # Top zones
            top_zones_stmt = (
                select(
                    ViolationLog.zone_name,
                    func.count(ViolationLog.id).label('count')
                )
                .group_by(ViolationLog.zone_name)
                .order_by(desc('count'))
                .limit(10)
            )
            top_zones_result = await session.execute(top_zones_stmt)
            top_zones = [
                {"zone_name": row[0], "violation_count": row[1]}
                for row in top_zones_result
            ]

            return {
                "total_violations": total_violations,
                "average_duration": round(float(avg_duration), 2) if avg_duration else 0,
                "top_users": top_users,
                "top_zones": top_zones
            }

    except Exception as e:
        logger.error(f"Error getting violation summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
