"""
Generic Message Clients
Support multiple message sources: Kafka, SSE, WebSocket, RabbitMQ, etc.
"""

from .base import MessageClient, MessageHandler
from .kafka_client import KafkaMessageClient
from .sse_client import SSEMessageClient
from .websocket_client import WebSocketMessageClient

__all__ = [
    'MessageClient',
    'MessageHandler',
    'KafkaMessageClient',
    'SSEMessageClient',
    'WebSocketMessageClient'
]
