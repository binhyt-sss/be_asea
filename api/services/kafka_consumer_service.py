"""
Kafka Consumer Service
Async Kafka consumer implementation using BaseConsumerService
"""

import asyncio
from typing import Optional
from loguru import logger

from api.services.base_consumer_service import BaseConsumerService
from utils.kafka_manager import KafkaAlertConsumer
from config.consumer_config import KafkaConsumerConfig


class KafkaConsumerService(BaseConsumerService):
    """
    Kafka implementation of MessageConsumerService

    Features:
    - Pure async/await (no threading)
    - Non-blocking message consumption
    - Graceful shutdown with cleanup
    - Wraps existing KafkaAlertConsumer
    """

    def __init__(self, config: KafkaConsumerConfig, message_buffer, broadcast_callback=None):
        """
        Initialize Kafka consumer service

        Args:
            config: KafkaConsumerConfig with Kafka settings
            message_buffer: Shared message buffer (deque)
            broadcast_callback: Optional callback for WebSocket broadcast
        """
        super().__init__(config, message_buffer, broadcast_callback)
        self.consumer: Optional[KafkaAlertConsumer] = None

    async def start(self):
        """Start Kafka consumer in async task"""
        if not self.config.enabled:
            logger.info("⚠️  Kafka is disabled in configuration")
            return

        if self._running:
            logger.warning("Kafka service already running")
            return

        try:
            # Initialize consumer
            self.consumer = KafkaAlertConsumer(kafka_config=self.config)
            logger.info(f"✅ Kafka consumer initialized: {self.config.bootstrap_servers}")

            # Save event loop reference for thread-safe callbacks
            self._event_loop = asyncio.get_running_loop()

            # Start background task
            self._running = True
            self._task = asyncio.create_task(self._consume_loop())
            logger.info("✅ Kafka consumer started")

        except Exception as e:
            logger.error(f"❌ Failed to start Kafka consumer: {e}")
            self._running = False
            raise

    async def _consume_loop(self):
        """Main consumption loop running in background"""
        logger.info(f"🔄 Kafka consumption loop started (topic: {self.config.topic})")

        while self._running:
            try:
                # Non-blocking consume with timeout
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.consumer.consume,
                    self._handle_message,  # Use base class handler
                    1.0  # timeout
                )

                # Small sleep to prevent CPU spinning
                await asyncio.sleep(0.01)

            except Exception as e:
                if self._running:  # Only log if not shutting down
                    logger.error(f"Error in Kafka consume loop: {e}")
                    await asyncio.sleep(1)  # Back off on error
                else:
                    break

        logger.info("Kafka consumption loop stopped")

    async def stop(self):
        """Stop Kafka consumer gracefully"""
        if not self._running:
            return

        logger.info("Stopping Kafka consumer...")
        self._running = False

        # Cancel background task
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        # Close consumer
        if self.consumer:
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.consumer.close
                )
                logger.info("✅ Kafka consumer closed")
            except Exception as e:
                logger.error(f"Error closing Kafka consumer: {e}")

        logger.info("✅ Kafka service stopped")

    def is_running(self) -> bool:
        """Check if Kafka consumer is running"""
        return self._running and self.consumer is not None

    def get_stats(self):
        """Get Kafka-specific statistics"""
        base_stats = super().get_stats()
        base_stats['config'] = {
            "enabled": self.config.enabled,
            "bootstrap_servers": self.config.bootstrap_servers,
            "topic": self.config.topic,
            "group_id": self.config.group_id
        }
        return base_stats
