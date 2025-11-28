"""
Server-Sent Events (SSE) Message Client
Connect to SSE endpoint and consume real-time events
"""

import json
import requests
from typing import Dict, Any, Optional
from loguru import logger

from clients.base import MessageClient, MessageHandler


class SSEMessageClient(MessageClient):
    """
    SSE message client implementation
    
    Example:
        client = SSEMessageClient({
            'url': 'http://localhost:8000/events',
            'headers': {'Authorization': 'Bearer token'}
        })
        client.connect()
        
        def handler(msg):
            print(f"Event: {msg}")
        
        client.consume(handler)
        client.close()
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize SSE client
        
        Args:
            config: SSE configuration
                - url: SSE endpoint URL (required)
                - headers: Optional HTTP headers
                - timeout: Request timeout in seconds
        """
        super().__init__(config)
        
        if not self.config.get('url'):
            raise ValueError("SSE client requires 'url' in config")
        
        self.url = self.config['url']
        self.headers = self.config.get('headers', {})
        self.timeout = self.config.get('timeout', 30)
        self.response = None
    
    def connect(self):
        """Connect to SSE endpoint"""
        try:
            # SSE connection is established on first consume
            self.connected = True
            logger.info(f"✅ SSE client ready: {self.url}")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup SSE client: {e}")
            raise ConnectionError(f"SSE setup failed: {e}")
    
    def consume(self, handler: MessageHandler, timeout: Optional[float] = None):
        """
        Consume SSE events
        
        Args:
            handler: Callback to process each event
            timeout: Not used for SSE (connection timeout set in config)
        """
        if not self.connected:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        try:
            # Stream SSE events
            with requests.get(
                self.url,
                headers=self.headers,
                stream=True,
                timeout=self.timeout
            ) as response:
                response.raise_for_status()
                self.response = response
                
                logger.info(f"🔄 SSE streaming started: {self.url}")
                
                # Parse SSE stream
                for line in response.iter_lines(decode_unicode=True):
                    if line:
                        # SSE format: "data: {json}"
                        if line.startswith('data:'):
                            data = line[5:].strip()  # Remove "data:" prefix
                            
                            try:
                                message = json.loads(data)
                                self._increment_message_count()
                                handler(message)
                                
                            except json.JSONDecodeError:
                                logger.warning(f"Invalid JSON in SSE: {data}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"SSE connection error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error consuming SSE events: {e}")
            raise
    
    def close(self):
        """Close SSE connection"""
        if self.response:
            try:
                self.response.close()
                self.connected = False
                logger.info(f"✅ SSE client closed ({self._message_count} events processed)")
            except Exception as e:
                logger.error(f"Error closing SSE connection: {e}")
