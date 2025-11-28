"""
Base Consumer Service (Abstract)
Define abstract interface for all message consumer services
"""

from abc import ABC, abstractmethod
from typing import Optional, Callable, Dict, Any
from collections import deque
import asyncio
from loguru import logger


class BaseConsumerService(ABC):
    """
    Abstract base class for async message consumer services

    All consumer implementations must:
    - Support async/await
    - Use shared message buffer (deque)
    - Support broadcast callback
    - Implement graceful start/stop

    Example:
        class MyConsumerService(BaseConsumerService):
            async def start(self): ...
            async def stop(self): ...
            def is_running(self) -> bool: ...
    """

    def __init__(
        self,
        config: Any,
        message_buffer: deque,
        broadcast_callback: Optional[Callable[[Dict[Any, Any]], None]] = None
    ):
        """
        Initialize consumer service

        Args:
            config: Consumer-specific configuration object
            message_buffer: Shared message buffer (deque) for storing messages
            broadcast_callback: Optional callback to broadcast messages to WebSocket clients
        """
        self.config = config
        self.message_buffer = message_buffer
        self.broadcast_callback = broadcast_callback

        # Internal state
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._message_count = 0
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None

    @abstractmethod
    async def start(self):
        """
        Start consuming messages

        Should:
        - Initialize connection/client
        - Create background task for consumption loop
        - Set _running = True
        - Handle initialization errors

        Raises:
            Exception: If start fails
        """
        pass

    @abstractmethod
    async def stop(self):
        """
        Stop consuming messages gracefully

        Should:
        - Set _running = False
        - Cancel background task
        - Close connections
        - Cleanup resources
        """
        pass

    @abstractmethod
    def is_running(self) -> bool:
        """
        Check if consumer is running

        Returns:
            True if consumer is actively running, False otherwise
        """
        pass

    def get_message_count(self) -> int:
        """
        Get total messages processed

        Returns:
            Number of messages processed since start
        """
        return self._message_count

    def get_stats(self) -> Dict[str, Any]:
        """
        Get service statistics

        Returns:
            Dictionary with service stats including:
            - running: bool
            - messages_processed: int
            - buffer_size: int
            - buffer_max: int
        """
        return {
            "running": self._running,
            "messages_processed": self._message_count,
            "buffer_size": len(self.message_buffer),
            "buffer_max": self.message_buffer.maxlen,
        }

    def _handle_message(self, message: Dict[Any, Any]):
        """
        Common message handling logic (used by all implementations)

        This method:
        1. Process custom business logic
        2. Adds message to buffer
        3. Broadcasts to WebSocket clients (if callback provided)
        4. Tracks message count
        5. Logs periodically

        Args:
            message: Message dict to handle
        """
        try:
            # ========================================================
            # CUSTOM BUSINESS LOGIC - THÊM LOGIC CỦA BẠN VÀO ĐÂY
            # ========================================================
            processed_message = self._process_business_logic(message)

            # Use processed message instead of original
            message = processed_message
            # ========================================================

            # Add to buffer
            self.message_buffer.append(message)
            self._message_count += 1

            # Broadcast to WebSocket clients if callback provided
            if self.broadcast_callback and self._event_loop and not self._event_loop.is_closed():
                try:
                    # Fire-and-forget: Schedule coroutine without waiting for result
                    # This is non-blocking and won't slow down message processing
                    asyncio.run_coroutine_threadsafe(
                        self.broadcast_callback(message),
                        self._event_loop
                    )
                    # Note: We intentionally don't call .result() to avoid blocking
                except Exception as e:
                    logger.error(f"Error scheduling broadcast: {e}")

            # Log periodically (every 100 messages)
            if self._message_count % 100 == 0:
                logger.info(f"📨 Messages processed: {self._message_count}")

        except Exception as e:
            logger.error(f"Error handling message: {e}")

    def _process_business_logic(self, message: Dict[Any, Any]) -> Dict[Any, Any]:
        """
        Process custom business logic for all messages

        This method uses MessageProcessor for real-time violation tracking:
        - Redis-based state tracking with TTL
        - Automatic violation detection
        - Alert de-bouncing (one alert per violation)

        Args:
            message: Original message from consumer

        Returns:
            Processed message (can be modified or enriched)
        """
        # Use MessageProcessor for real-time tracking
        from api.services.message_processor import MessageProcessor
        import asyncio

        # Run async process in event loop
        # Create task and wait for completion synchronously
        future = asyncio.run_coroutine_threadsafe(
            MessageProcessor.process(message),
            self._event_loop
        )
        processed_message = future.result(timeout=5.0)  # 5 second timeout

        return processed_message
