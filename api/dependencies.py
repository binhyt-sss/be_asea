"""
FastAPI Dependencies
Shared dependencies for dependency injection
"""

from collections import deque

# Global instances
_message_buffer = deque(maxlen=100)


def get_message_buffer() -> deque:
    """Dependency to get Kafka message buffer"""
    return _message_buffer
