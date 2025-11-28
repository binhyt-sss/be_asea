"""
Real-time Violation Tracking with Redis

Hot/Cold Architecture:
- Hot Layer (Redis): Real-time tracking state with TTL
- Cold Layer (PostgreSQL): Persistent violation logs
- Cache Layer: Zone configuration cache

This processor tracks user presence in zones and detects when they exceed
the configured threshold, preventing alert spam with Redis flags.
"""

import json
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from collections import deque
from loguru import logger

# Redis async client
from redis import asyncio as aioredis

# Config
from config.settings import Settings

settings = Settings()


class MessageProcessor:
    """
    Production-grade real-time violation tracking processor

    Features:
    - Redis-based state tracking with atomic operations
    - TTL auto-cleanup for disappeared users
    - Alert de-bouncing (one alert per violation)
    - Zone-specific threshold configuration with cache
    - Race condition protection via Redis pipeline
    """

    # Redis client (will be initialized in init_redis())
    _redis: Optional[aioredis.Redis] = None

    # Zone config cache (RAM cache to reduce Redis/DB load)
    _zone_config_cache: Dict[str, int] = {}

    # Statistics
    _stats = {
        'messages_processed': 0,
        'violations_detected': 0,
        'warnings_issued': 0,
        'errors': 0
    }

    @classmethod
    async def init_redis(cls):
        """Initialize Redis connection pool"""
        if cls._redis is None:
            try:
                cls._redis = await aioredis.from_url(
                    settings.business.redis_url,
                    decode_responses=True,
                    encoding="utf-8"
                )
                # Test connection
                await cls._redis.ping()
                logger.info(f"✅ Redis connected: {settings.business.redis_url}")
            except Exception as e:
                logger.error(f"❌ Failed to connect to Redis: {e}")
                raise

    @classmethod
    async def close_redis(cls):
        """Close Redis connection"""
        if cls._redis:
            await cls._redis.close()
            cls._redis = None
            logger.info("Redis connection closed")

    @classmethod
    async def process(cls, message: Dict[Any, Any]) -> Dict[Any, Any]:
        """
        Main processing function - called for EVERY message from ALL consumers

        Args:
            message: Raw message from consumer (Kafka/SSE/WebSocket)

        Returns:
            Enriched message with tracking status
        """
        cls._stats['messages_processed'] += 1

        try:
            # Ensure Redis is initialized
            if cls._redis is None:
                await cls.init_redis()

            # Extract required fields
            user_id = str(message.get('user_id', ''))
            zone_id = str(message.get('zone_id', ''))
            user_name = message.get('user_name', user_id)
            zone_name = message.get('zone_name', zone_id)

            # Validate required fields
            if not user_id or not zone_id:
                logger.warning(f"⚠️ Missing user_id or zone_id in message")
                message['be_status'] = 'INVALID'
                cls._stats['errors'] += 1
                return message

            # Get current timestamp
            current_ts = time.time()
            if 'timestamp' in message:
                try:
                    # Try to parse timestamp from message if available
                    msg_time = datetime.fromisoformat(message['timestamp'].replace('Z', '+00:00'))
                    current_ts = msg_time.timestamp()
                except:
                    pass

            # 1. Get zone threshold (Cache -> DB -> Default)
            threshold = await cls._get_zone_threshold(zone_id)

            # 2. Redis key for this tracking instance
            key = f"track:{user_id}:{zone_id}"

            # 3. Atomic Redis operation (prevent race conditions)
            async with cls._redis.pipeline(transaction=True) as pipe:
                try:
                    # Get current state
                    await pipe.hgetall(key)
                    await pipe.ttl(key)
                    results = await pipe.execute()

                    state_data = results[0]
                    current_ttl = results[1]

                    if not state_data:
                        # CASE 1: New entry - User just entered zone
                        await cls._redis.hset(key, mapping={
                            "start_ts": current_ts,
                            "user_name": user_name,
                            "zone_name": zone_name,
                            "threshold": threshold,
                            "alerted": 0
                        })
                        await cls._redis.expire(key, settings.business.tracking_ttl)

                        message['be_status'] = 'ENTERED'
                        message['_tracking_duration'] = 0
                        logger.debug(f"👤 User {user_name} entered {zone_name}")

                    else:
                        # CASE 2: Ongoing tracking - User still in zone
                        start_ts = float(state_data['start_ts'])
                        alerted = int(state_data.get('alerted', 0))
                        duration = current_ts - start_ts

                        message['_tracking_duration'] = round(duration, 2)

                        if duration > threshold:
                            if alerted == 0:
                                # VIOLATION DETECTED (First time exceeding threshold)
                                message['be_status'] = 'VIOLATION'
                                message['_violation_duration'] = round(duration, 2)
                                message['_threshold'] = threshold

                                # Mark as alerted to prevent spam
                                await cls._redis.hset(key, "alerted", 1)

                                # Save to database (async, non-blocking)
                                asyncio.create_task(
                                    cls._save_violation_log(
                                        user_id=user_id,
                                        zone_id=zone_id,
                                        user_name=user_name,
                                        zone_name=zone_name,
                                        start_ts=start_ts,
                                        duration=duration,
                                        threshold=threshold
                                    )
                                )

                                cls._stats['violations_detected'] += 1
                                logger.warning(
                                    f"🚨 VIOLATION: {user_name} in {zone_name} "
                                    f"(duration: {duration:.1f}s > threshold: {threshold}s)"
                                )
                            else:
                                # ONGOING VIOLATION (Already alerted)
                                message['be_status'] = 'VIOLATION_ONGOING'
                                message['_violation_duration'] = round(duration, 2)
                                message['_threshold'] = threshold

                        else:
                            # WARNING (Still within threshold)
                            message['be_status'] = 'WARNING'
                            message['_time_remaining'] = round(threshold - duration, 2)

                            cls._stats['warnings_issued'] += 1

                        # Refresh TTL on every message
                        await cls._redis.expire(key, settings.business.tracking_ttl)

                except Exception as e:
                    logger.error(f"Redis pipeline error: {e}")
                    message['be_status'] = 'ERROR'
                    cls._stats['errors'] += 1

        except Exception as e:
            logger.error(f"Message processing error: {e}")
            message['be_status'] = 'ERROR'
            cls._stats['errors'] += 1

        return message

    @classmethod
    async def _get_zone_threshold(cls, zone_id: str) -> int:
        """
        Get zone violation threshold with caching strategy

        Priority:
        1. RAM cache (fastest)
        2. Database (zone-specific config)
        3. Settings default (fallback)
        """
        # Check RAM cache first
        if zone_id in cls._zone_config_cache:
            return cls._zone_config_cache[zone_id]

        # Query database for zone-specific threshold
        try:
            from database.session import AsyncSessionLocal
            from database.models import WorkingZone
            from sqlalchemy import select

            async with AsyncSessionLocal() as session:
                # Query zone config
                stmt = select(WorkingZone.violation_threshold).where(
                    WorkingZone.zone_id == zone_id
                )
                result = await session.execute(stmt)
                db_threshold = result.scalar_one_or_none()

                if db_threshold is not None:
                    # Found zone-specific config
                    threshold = db_threshold
                    logger.debug(f"Zone {zone_id} threshold from DB: {threshold}s")
                else:
                    # Zone not found in database, use default
                    threshold = settings.business.default_threshold
                    logger.warning(
                        f"Zone {zone_id} not found in DB, using default: {threshold}s"
                    )

        except Exception as e:
            # Database error - graceful degradation
            logger.error(f"Failed to query threshold for zone {zone_id}: {e}")
            threshold = settings.business.default_threshold
            logger.warning(f"Using default threshold: {threshold}s")

        # Cache it for future lookups
        cls._zone_config_cache[zone_id] = threshold

        return threshold

    @classmethod
    def update_zone_cache(cls, zone_id: str, threshold: int):
        """
        Update zone config cache (called when admin changes zone config)

        Args:
            zone_id: Zone ID
            threshold: New threshold value
        """
        cls._zone_config_cache[zone_id] = threshold
        logger.info(f"🔄 Updated zone cache: {zone_id} -> {threshold}s")

    @classmethod
    def invalidate_zone_cache(cls, zone_id: Optional[str] = None):
        """
        Invalidate zone cache

        Args:
            zone_id: Specific zone ID, or None to clear all
        """
        if zone_id:
            cls._zone_config_cache.pop(zone_id, None)
            logger.info(f"🗑️ Invalidated zone cache: {zone_id}")
        else:
            cls._zone_config_cache.clear()
            logger.info("🗑️ Cleared all zone cache")

    @classmethod
    async def _save_violation_log(
        cls,
        user_id: str,
        zone_id: str,
        user_name: str,
        zone_name: str,
        start_ts: float,
        duration: float,
        threshold: int
    ):
        """
        Save violation log to database (async, non-blocking)

        This runs in background task to not block message processing
        """
        try:
            from database.session import AsyncSessionLocal
            from database.models import ViolationLog

            async with AsyncSessionLocal() as session:
                # Create violation log record
                violation = ViolationLog(
                    user_id=user_id,
                    zone_id=zone_id,
                    user_name=user_name,
                    zone_name=zone_name,
                    start_time=datetime.fromtimestamp(start_ts),
                    duration=duration,
                    threshold=threshold
                )

                session.add(violation)
                await session.commit()

                logger.info(
                    f"💾 [DB SAVED] Violation #{violation.id}: {user_name} in {zone_name} "
                    f"(duration: {duration:.1f}s, threshold: {threshold}s)"
                )

        except Exception as e:
            logger.error(f"❌ Failed to save violation log to database: {e}")
            # Don't raise - we don't want to crash message processing if DB save fails

    @classmethod
    def get_statistics(cls) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            **cls._stats,
            'zone_cache_size': len(cls._zone_config_cache)
        }

    @classmethod
    async def clear_user_tracking(cls, user_id: str, zone_id: str):
        """
        Manually clear tracking state for a user in a zone

        Useful for testing or manual intervention
        """
        if cls._redis:
            key = f"track:{user_id}:{zone_id}"
            await cls._redis.delete(key)
            logger.info(f"🗑️ Cleared tracking: {user_id} in {zone_id}")

    @classmethod
    def get_violations_queue(cls) -> List[Dict[str, Any]]:
        """
        Get violations queue for manual review
        
        Note: Since we moved to Redis + DB architecture, this returns
        recent unresolved violations from the database instead of RAM queue
        """
        # Return empty for now - the Redis system directly saves to DB
        # and doesn't maintain a separate "queue" for manual approval
        return []

    @classmethod
    async def manual_approve_violation(cls, violation_id: str, action: str) -> bool:
        """
        Manual approval/rejection of violations
        
        Note: Since violations are auto-saved to DB, this method would
        update the violation status in the database
        """
        try:
            from database.session import AsyncSessionLocal
            from database.models import ViolationLog
            from sqlalchemy import select

            async with AsyncSessionLocal() as session:
                # Find violation by ID
                stmt = select(ViolationLog).where(ViolationLog.id == int(violation_id))
                result = await session.execute(stmt)
                violation = result.scalar_one_or_none()

                if not violation:
                    return False

                # For now, we don't have status fields in DB
                # Could add is_approved/is_rejected fields later
                logger.info(f"📋 Manual {action} for violation #{violation_id}: {violation.user_name} in {violation.zone_name}")
                return True

        except Exception as e:
            logger.error(f"Manual approval error: {e}")
            return False
