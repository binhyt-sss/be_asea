"""
Server-Sent Events (SSE) Consumer Service
Async SSE consumer implementation using BaseConsumerService
"""

import asyncio
import aiohttp
import json
from typing import Optional
from loguru import logger

from api.services.base_consumer_service import BaseConsumerService
from config.consumer_config import SSEConsumerConfig


class SSEConsumerService(BaseConsumerService):
    """
    SSE implementation of MessageConsumerService

    Features:
    - Full async with aiohttp
    - Auto-reconnect on disconnect
    - Exponential backoff
    - SSE format parsing (data: {json})
    """

    def __init__(self, config: SSEConsumerConfig, message_buffer, broadcast_callback=None):
        """
        Initialize SSE consumer service

        Args:
            config: SSEConsumerConfig with SSE settings
            message_buffer: Shared message buffer (deque)
            broadcast_callback: Optional callback for WebSocket broadcast
        """
        super().__init__(config, message_buffer, broadcast_callback)
        self.session: Optional[aiohttp.ClientSession] = None
        self.response: Optional[aiohttp.ClientResponse] = None
        self._retry_count = 0

    async def start(self):
        """Start SSE consumer"""
        if not self.config.enabled:
            logger.info("⚠️  SSE is disabled in configuration")
            return

        if self._running:
            logger.warning("SSE service already running")
            return

        try:
            self.session = aiohttp.ClientSession()
            logger.info(f"✅ SSE session initialized: {self.config.url}")

            self._running = True
            self._task = asyncio.create_task(self._consume_loop())
            logger.info("✅ SSE consumer started")

        except Exception as e:
            logger.error(f"❌ Failed to start SSE consumer: {e}")
            self._running = False
            raise

    async def _consume_loop(self):
        """SSE-specific consumption loop with auto-reconnect"""
        logger.info(f"🔄 SSE consumption loop started (url: {self.config.url})")

        while self._running:
            try:
                # Connect to SSE endpoint
                async with self.session.get(
                    self.config.url,
                    headers=self.config.headers,
                    timeout=aiohttp.ClientTimeout(total=None)  # No timeout for streaming
                ) as response:
                    self.response = response

                    if response.status != 200:
                        logger.error(f"SSE connection failed: HTTP {response.status}")
                        await self._handle_reconnect()
                        continue

                    logger.info(f"✅ Connected to SSE endpoint: {self.config.url}")
                    self._retry_count = 0  # Reset retry count on successful connection

                    # Stream SSE events
                    async for line in response.content:
                        if not self._running:
                            break

                        line = line.decode('utf-8').strip()

                        # Parse SSE format: "data: {json}"
                        if line.startswith('data:'):
                            data = line[5:].strip()  # Remove "data:" prefix

                            try:
                                message = json.loads(data)
                                self._handle_message(message)  # Use base class handler

                            except json.JSONDecodeError as e:
                                logger.warning(f"Invalid JSON in SSE: {data[:100]}...")

            except aiohttp.ClientError as e:
                if self._running:
                    logger.error(f"SSE connection error: {e}")
                    await self._handle_reconnect()
                else:
                    break

            except Exception as e:
                if self._running:
                    logger.error(f"Error in SSE consume loop: {e}")
                    await self._handle_reconnect()
                else:
                    break

        logger.info("SSE consumption loop stopped")

    async def _handle_reconnect(self):
        """
        Handle reconnection with exponential backoff

        Implements retry logic with configurable max retries
        """
        if not self._running:
            return

        self._retry_count += 1

        # Check max retries (if configured)
        if self.config.max_retries > 0 and self._retry_count > self.config.max_retries:
            logger.error(f"❌ Max retries ({self.config.max_retries}) reached. Stopping SSE consumer.")
            self._running = False
            return

        # Exponential backoff with cap
        delay = min(self.config.retry_delay * (2 ** min(self._retry_count - 1, 5)), 60)
        logger.info(f"⏳ Retrying SSE connection in {delay}s (attempt {self._retry_count})...")
        await asyncio.sleep(delay)

    async def stop(self):
        """Stop SSE consumer gracefully"""
        if not self._running:
            return

        logger.info("Stopping SSE consumer...")
        self._running = False

        # Cancel background task
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        # Close response and session
        if self.response:
            self.response.close()

        if self.session:
            await self.session.close()
            logger.info("✅ SSE session closed")

        logger.info("✅ SSE service stopped")

    def is_running(self) -> bool:
        """Check if SSE consumer is running"""
        return self._running and self.session is not None

    def get_stats(self):
        """Get SSE-specific statistics"""
        base_stats = super().get_stats()
        base_stats['config'] = {
            'enabled': self.config.enabled,
            'url': self.config.url,
            'retry_delay': self.config.retry_delay,
            'retry_count': self._retry_count
        }
        return base_stats
