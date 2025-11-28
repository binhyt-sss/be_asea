"""
Consumer Factory
Creates appropriate consumer service based on configuration
"""

from typing import Optional, Callable, Dict, Any
from collections import deque
from loguru import logger

from config.consumer_config import ConsumerSettings
from api.services.base_consumer_service import BaseConsumerService
from api.services.kafka_consumer_service import KafkaConsumerService
from api.services.sse_consumer_service import SSEConsumerService
from api.services.websocket_consumer_service import WebSocketConsumerService


class ConsumerFactory:
    """
    Factory for creating consumer services based on configuration

    Usage:
        settings = get_settings()
        consumer = ConsumerFactory.create(
            consumer_settings=settings.consumer,
            message_buffer=buffer,
            broadcast_callback=broadcast_fn
        )
        await consumer.start()
    """

    @staticmethod
    def create(
        consumer_settings: ConsumerSettings,
        message_buffer: deque,
        broadcast_callback: Optional[Callable[[Dict[Any, Any]], None]] = None
    ) -> BaseConsumerService:
        """
        Create consumer service based on configuration

        Args:
            consumer_settings: ConsumerSettings from configuration
            message_buffer: Shared message buffer (deque)
            broadcast_callback: Optional callback for WebSocket broadcast

        Returns:
            BaseConsumerService implementation (Kafka, SSE, or WebSocket)

        Raises:
            ValueError: If consumer type is unknown

        Example:
            factory = ConsumerFactory()
            consumer = factory.create(settings.consumer, buffer, callback)
            await consumer.start()
        """

        consumer_type = consumer_settings.consumer_type
        config = consumer_settings.get_active_config()

        logger.info(f"🏭 Creating consumer service: {consumer_type.upper()}")

        if consumer_type == 'kafka':
            return KafkaConsumerService(
                config=config,
                message_buffer=message_buffer,
                broadcast_callback=broadcast_callback
            )

        elif consumer_type == 'sse':
            return SSEConsumerService(
                config=config,
                message_buffer=message_buffer,
                broadcast_callback=broadcast_callback
            )

        elif consumer_type == 'websocket':
            return WebSocketConsumerService(
                config=config,
                message_buffer=message_buffer,
                broadcast_callback=broadcast_callback
            )

        else:
            raise ValueError(f"Unknown consumer type: {consumer_type}")

    @staticmethod
    def list_available_consumers() -> list:
        """
        List all available consumer types

        Returns:
            List of available consumer type strings
        """
        return ['kafka', 'sse', 'websocket']
