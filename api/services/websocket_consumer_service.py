"""
WebSocket Consumer Service
Async WebSocket consumer implementation using BaseConsumerService
"""

import asyncio
import aiohttp
import json
from typing import Optional
from loguru import logger

from api.services.base_consumer_service import BaseConsumerService
from config.consumer_config import WebSocketConsumerConfig


class WebSocketConsumerService(BaseConsumerService):
    """
    WebSocket implementation of MessageConsumerService

    Features:
    - Full async with aiohttp
    - Auto-reconnect on disconnect
    - Message type filtering
    - Ping/pong heartbeat
    """

    def __init__(self, config: WebSocketConsumerConfig, message_buffer, broadcast_callback=None):
        """
        Initialize WebSocket consumer service

        Args:
            config: WebSocketConsumerConfig with WebSocket settings
            message_buffer: Shared message buffer (deque)
            broadcast_callback: Optional callback for WebSocket broadcast
        """
        super().__init__(config, message_buffer, broadcast_callback)
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._retry_count = 0

    async def start(self):
        """Start WebSocket consumer"""
        if not self.config.enabled:
            logger.info("⚠️  WebSocket is disabled in configuration")
            return

        if self._running:
            logger.warning("WebSocket service already running")
            return

        try:
            self.session = aiohttp.ClientSession()
            logger.info(f"✅ WebSocket session initialized: {self.config.url}")

            self._running = True
            self._task = asyncio.create_task(self._consume_loop())
            logger.info("✅ WebSocket consumer started")

        except Exception as e:
            logger.error(f"❌ Failed to start WebSocket consumer: {e}")
            self._running = False
            raise

    async def _consume_loop(self):
        """WebSocket-specific consumption loop with auto-reconnect"""
        logger.info(f"🔄 WebSocket consumption loop started (url: {self.config.url})")

        while self._running:
            try:
                # Connect to WebSocket endpoint
                async with self.session.ws_connect(
                    self.config.url,
                    headers=self.config.headers,
                    heartbeat=self.config.ping_interval,
                    timeout=aiohttp.ClientTimeout(total=self.config.ping_timeout)
                ) as ws:
                    self.ws = ws
                    logger.info(f"✅ Connected to WebSocket: {self.config.url}")
                    self._retry_count = 0  # Reset retry count on successful connection

                    # Receive messages
                    async for msg in ws:
                        if not self._running:
                            break

                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                data = json.loads(msg.data)

                                # Handle different message types
                                msg_type = data.get('type')

                                if msg_type == 'alert':
                                    # Extract actual alert data
                                    alert_data = data.get('data', data)
                                    self._handle_message(alert_data)

                                elif msg_type in ['history', 'system']:
                                    # Skip system messages
                                    logger.debug(f"Skipping {msg_type} message")

                                else:
                                    # Treat as regular message
                                    self._handle_message(data)

                            except json.JSONDecodeError:
                                logger.warning(f"Invalid JSON from WebSocket: {msg.data[:100]}...")

                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            logger.error(f"WebSocket error: {ws.exception()}")
                            break

                        elif msg.type == aiohttp.WSMsgType.CLOSED:
                            logger.warning("WebSocket connection closed by server")
                            break

            except aiohttp.ClientError as e:
                if self._running:
                    logger.error(f"WebSocket connection error: {e}")
                    await self._handle_reconnect()
                else:
                    break

            except Exception as e:
                if self._running:
                    logger.error(f"Error in WebSocket consume loop: {e}")
                    await self._handle_reconnect()
                else:
                    break

        logger.info("WebSocket consumption loop stopped")

    async def _handle_reconnect(self):
        """
        Handle reconnection with delay

        Implements retry logic with configurable delay
        """
        if not self._running:
            return

        self._retry_count += 1
        delay = self.config.reconnect_delay

        logger.info(f"⏳ Retrying WebSocket connection in {delay}s (attempt {self._retry_count})...")
        await asyncio.sleep(delay)

    async def stop(self):
        """Stop WebSocket consumer gracefully"""
        if not self._running:
            return

        logger.info("Stopping WebSocket consumer...")
        self._running = False

        # Cancel background task
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        # Close WebSocket and session
        if self.ws and not self.ws.closed:
            await self.ws.close()

        if self.session:
            await self.session.close()
            logger.info("✅ WebSocket session closed")

        logger.info("✅ WebSocket service stopped")

    def is_running(self) -> bool:
        """Check if WebSocket consumer is running"""
        return self._running and self.ws is not None and not self.ws.closed

    def get_stats(self):
        """Get WebSocket-specific statistics"""
        base_stats = super().get_stats()
        base_stats['config'] = {
            'enabled': self.config.enabled,
            'url': self.config.url,
            'reconnect_delay': self.config.reconnect_delay,
            'retry_count': self._retry_count
        }
        return base_stats
