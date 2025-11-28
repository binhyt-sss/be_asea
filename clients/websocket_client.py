"""
WebSocket Message Client
Connect to WebSocket endpoint and consume real-time messages
"""

import json
import asyncio
import websockets
from typing import Dict, Any, Optional
from loguru import logger

from clients.base import MessageClient, MessageHandler


class WebSocketMessageClient(MessageClient):
    """
    WebSocket message client implementation
    
    Example:
        client = WebSocketMessageClient({
            'url': 'ws://localhost:8000/ws/alerts'
        })
        client.connect()
        
        def handler(msg):
            if msg['type'] == 'alert':
                print(f"Alert: {msg['data']}")
        
        client.consume(handler)
        client.close()
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize WebSocket client
        
        Args:
            config: WebSocket configuration
                - url: WebSocket URL (required, must start with ws:// or wss://)
                - headers: Optional connection headers
                - ping_interval: Ping interval in seconds
                - ping_timeout: Ping timeout in seconds
        """
        super().__init__(config)
        
        if not self.config.get('url'):
            raise ValueError("WebSocket client requires 'url' in config")
        
        url = self.config['url']
        if not (url.startswith('ws://') or url.startswith('wss://')):
            raise ValueError("WebSocket URL must start with ws:// or wss://")
        
        self.url = url
        self.extra_headers = self.config.get('headers', {})
        self.ping_interval = self.config.get('ping_interval', 20)
        self.ping_timeout = self.config.get('ping_timeout', 10)
        self.websocket = None
    
    def connect(self):
        """Setup WebSocket client (actual connection happens in consume)"""
        try:
            self.connected = True
            logger.info(f"✅ WebSocket client ready: {self.url}")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup WebSocket client: {e}")
            raise ConnectionError(f"WebSocket setup failed: {e}")
    
    def consume(self, handler: MessageHandler, timeout: Optional[float] = None):
        """
        Consume WebSocket messages
        
        Args:
            handler: Callback to process each message
            timeout: Not used for WebSocket
        """
        if not self.connected:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        # Run async consume in sync context
        asyncio.run(self._async_consume(handler))
    
    async def _async_consume(self, handler: MessageHandler):
        """Async consume implementation"""
        try:
            async with websockets.connect(
                self.url,
                extra_headers=self.extra_headers,
                ping_interval=self.ping_interval,
                ping_timeout=self.ping_timeout
            ) as websocket:
                self.websocket = websocket
                logger.info(f"🔄 WebSocket connected: {self.url}")
                
                async for message in websocket:
                    try:
                        # Parse JSON message
                        data = json.loads(message)
                        self._increment_message_count()
                        handler(data)
                        
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON from WebSocket: {message}")
                        
        except websockets.exceptions.WebSocketException as e:
            logger.error(f"WebSocket error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error consuming WebSocket messages: {e}")
            raise
    
    def close(self):
        """Close WebSocket connection"""
        if self.websocket:
            try:
                # Close happens automatically with context manager
                self.connected = False
                logger.info(f"✅ WebSocket client closed ({self._message_count} messages processed)")
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")
