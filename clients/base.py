"""
Base Message Client Interface
Define abstract interface for all message sources
"""

from abc import ABC, abstractmethod
from typing import Callable, Dict, Any, Optional
from loguru import logger


# Type alias for message handler callback
MessageHandler = Callable[[Dict[str, Any]], None]


class MessageClient(ABC):
    """
    Abstract base class for message clients
    
    Implement this interface to support different message sources:
    - Kafka
    - Server-Sent Events (SSE)
    - WebSocket
    - RabbitMQ
    - Redis Pub/Sub
    - etc.
    
    Example:
        class MyClient(MessageClient):
            def connect(self): ...
            def consume(self, handler): ...
            def close(self): ...
        
        client = MyClient()
        client.connect()
        client.consume(lambda msg: print(msg))
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize client with configuration
        
        Args:
            config: Client-specific configuration
        """
        self.config = config or {}
        self.connected = False
        self._message_count = 0
    
    @abstractmethod
    def connect(self):
        """
        Establish connection to message source
        
        Raises:
            ConnectionError: If connection fails
        """
        pass
    
    @abstractmethod
    def consume(self, handler: MessageHandler, timeout: Optional[float] = None):
        """
        Consume messages and call handler for each message
        
        Args:
            handler: Callback function to process messages
            timeout: Optional timeout for blocking consume
        
        Example:
            def my_handler(message):
                print(f"Received: {message}")
            
            client.consume(my_handler, timeout=1.0)
        """
        pass
    
    @abstractmethod
    def close(self):
        """
        Close connection and cleanup resources
        """
        pass
    
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self.connected
    
    def get_message_count(self) -> int:
        """Get total messages processed"""
        return self._message_count
    
    def _increment_message_count(self):
        """Increment message counter (internal use)"""
        self._message_count += 1
        if self._message_count % 100 == 0:
            logger.info(f"📊 {self.__class__.__name__} processed {self._message_count} messages")
