"""
Custom Message Processor
Hybrid approach: Auto-process basic tasks + Provide endpoints for advanced processing
"""

import time
import asyncio
from typing import Dict, Any, List
from datetime import datetime
from loguru import logger
from collections import deque


class MessageProcessor:
    """
    Custom business logic processor

    HYBRID APPROACH:
    1. Auto-process: Basic validation, enrichment, simple alerts
    2. Endpoints: Manual processing for complex tasks
    """

    # Store violations for manual review
    _violations_queue: deque = deque(maxlen=100)

    @staticmethod
    def process(message: Dict[Any, Any]) -> Dict[Any, Any]:
        """
        Main processing function - AUTO PROCESSING

        This runs AUTOMATICALLY for EVERY message
        """
        try:
            # 1. VALIDATE (auto)
            if not MessageProcessor._validate(message):
                logger.error(f"❌ Invalid message: {message}")
                return message

            # 2. ENRICH (auto)
            message = MessageProcessor._enrich(message)

            # 3. AUTO-PROCESS by status
            status = message.get('status')

            if status == 'violation':
                # Auto: Log và add to queue for manual review
                MessageProcessor._auto_process_violation(message)

            elif status == 'authorized':
                # Auto: Just log
                logger.info(f"✅ AUTHORIZED: {message['user_name']}")

            # 4. AUTO SAVE (basic info only)
            asyncio.create_task(MessageProcessor._auto_save_basic(message))

            return message

        except Exception as e:
            logger.error(f"Error in message processor: {e}")
            return message

    # ================================================================
    # AUTO PROCESSING (runs immediately)
    # ================================================================

    @staticmethod
    def _validate(message: Dict[Any, Any]) -> bool:
        """Validate message schema"""
        required = ['user_id', 'zone_id', 'status', 'timestamp']
        return all(field in message for field in required)

    @staticmethod
    def _enrich(message: Dict[Any, Any]) -> Dict[Any, Any]:
        """Enrich message with additional data"""
        message['_processed_at'] = time.time()
        message['_server_timestamp'] = datetime.now().isoformat()

        # Calculate severity
        iop = message.get('iop', 0)
        threshold = message.get('threshold', 0.5)

        if iop > threshold * 1.5:
            message['_severity'] = 'HIGH'
        elif iop > threshold * 1.2:
            message['_severity'] = 'MEDIUM'
        else:
            message['_severity'] = 'LOW'

        return message

    @staticmethod
    def _auto_process_violation(message: Dict[Any, Any]):
        """Auto-process violations"""
        logger.warning(
            f"🚨 VIOLATION: {message['user_name']} "
            f"in {message['zone_name']} "
            f"[Severity: {message.get('_severity', 'UNKNOWN')}]"
        )

        # Add to queue for manual review (via endpoint)
        MessageProcessor._violations_queue.append(message)

        # Auto-send simple notification (không cần approval)
        if message.get('_severity') == 'HIGH':
            asyncio.create_task(MessageProcessor._send_simple_alert(message))

    @staticmethod
    async def _auto_save_basic(message: Dict[Any, Any]):
        """Auto-save basic info to database"""
        try:
            # TODO: Implement basic save
            # Save user_id, zone_id, status, timestamp only
            logger.debug(f"💾 Auto-saved basic info: {message['user_id']}")
        except Exception as e:
            logger.error(f"Failed to auto-save: {e}")

    @staticmethod
    async def _send_simple_alert(message: Dict[Any, Any]):
        """Send simple alert (không cần approval)"""
        try:
            # TODO: Send simple Telegram/Email
            logger.info(f"📤 Sent simple alert: {message['user_name']}")
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")

    # ================================================================
    # MANUAL PROCESSING (via endpoints)
    # ================================================================

    @staticmethod
    def get_violations_queue() -> List[Dict[Any, Any]]:
        """Get violations waiting for manual review"""
        return list(MessageProcessor._violations_queue)

    @staticmethod
    async def manual_approve_violation(violation_id: str, action: str) -> bool:
        """
        Manually approve/reject violation

        Args:
            violation_id: User ID from violation
            action: 'approve' or 'reject'

        Returns:
            True if processed successfully
        """
        try:
            # Find violation in queue
            violation = None
            for v in MessageProcessor._violations_queue:
                if v.get('user_id') == violation_id:
                    violation = v
                    break

            if not violation:
                logger.warning(f"Violation not found: {violation_id}")
                return False

            if action == 'approve':
                # Do advanced processing
                await MessageProcessor._advanced_save(violation)
                await MessageProcessor._send_advanced_alert(violation)
                logger.info(f"✅ Violation APPROVED: {violation_id}")

            elif action == 'reject':
                # Mark as false positive
                logger.info(f"❌ Violation REJECTED: {violation_id}")

            # Remove from queue
            MessageProcessor._violations_queue.remove(violation)

            return True

        except Exception as e:
            logger.error(f"Failed to process violation: {e}")
            return False

    @staticmethod
    async def _advanced_save(message: Dict[Any, Any]):
        """Save complete violation data with all details"""
        try:
            # TODO: Save full violation details
            logger.info(f"💾 Saved full violation: {message['user_id']}")
        except Exception as e:
            logger.error(f"Failed to save violation: {e}")

    @staticmethod
    async def _send_advanced_alert(message: Dict[Any, Any]):
        """Send detailed alert with images, etc."""
        try:
            # TODO: Send detailed Telegram/Email with images
            logger.info(f"📤 Sent detailed alert: {message['user_id']}")
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")

    # ================================================================
    # ANALYTICS & REPORTS (via endpoints)
    # ================================================================

    @staticmethod
    def get_statistics() -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            "pending_violations": len(MessageProcessor._violations_queue),
            "queue_capacity": MessageProcessor._violations_queue.maxlen,
        }
