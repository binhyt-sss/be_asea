"""
Violations Management API
Manual review and processing of violations
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

from api.services.message_processor import MessageProcessor


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
            pending_violations=stats['pending_violations'],
            queue_capacity=stats['queue_capacity']
        )

    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
