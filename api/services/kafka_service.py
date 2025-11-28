"""
Kafka Background Service (Async Architecture)
Manages Kafka consumer with asyncio for better integration with FastAPI
"""

import asyncio
from typing import Optional, Callable, Dict, Any
from collections import deque
from loguru import logger

from utils.kafka_manager import KafkaAlertConsumer
from config import KafkaSettings


class KafkaService:
    """
    Async Kafka consumer service
    
    Features:
    - Pure async/await (no threading)
    - Non-blocking message consumption
    - Graceful shutdown with cleanup
    - Message buffer management
    - Event broadcasting support
    """
    
    def __init__(
        self, 
        kafka_config: KafkaSettings, 
        message_buffer: deque,
        broadcast_callback: Optional[Callable[[Dict[Any, Any]], None]] = None
    ):
        """
        Initialize Kafka service
        
        Args:
            kafka_config: Kafka configuration
            message_buffer: Shared message buffer for storing messages
            broadcast_callback: Optional callback to broadcast messages to WebSocket clients
        """
        self.kafka_config = kafka_config
        self.message_buffer = message_buffer
        self.broadcast_callback = broadcast_callback
        
        self.consumer: Optional[KafkaAlertConsumer] = None
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._message_count = 0
    
    async def start(self):
        """Start Kafka consumer in async task"""
        if not self.kafka_config.enabled:
            logger.info("⚠️  Kafka is disabled in configuration")
            return
        
        if self._running:
            logger.warning("Kafka service already running")
            return
        
        try:
            # Initialize consumer
            self.consumer = KafkaAlertConsumer(kafka_config=self.kafka_config)
            logger.info(f"✅ Kafka consumer initialized: {self.kafka_config.bootstrap_servers}")
            
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
        logger.info(f"🔄 Kafka consumption loop started (topic: {self.kafka_config.topic})")
        
        while self._running:
            try:
                # Non-blocking consume with timeout
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.consumer.consume,
                    self._handle_message,
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
    
    def _handle_message(self, message: Dict[Any, Any]):
        """
        Handle incoming Kafka message
        
        Args:
            message: Parsed message from Kafka
        """
        try:
            # Add to buffer
            self.message_buffer.append(message)
            self._message_count += 1
            
            # Broadcast to WebSocket clients if callback provided
            if self.broadcast_callback:
                try:
                    self.broadcast_callback(message)
                except Exception as e:
                    logger.error(f"Error in broadcast callback: {e}")
            
            # Log periodically
            if self._message_count % 100 == 0:
                logger.info(f"📨 Kafka messages processed: {self._message_count}")
                
        except Exception as e:
            logger.error(f"Error handling Kafka message: {e}")
    
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
    
    def get_message_count(self) -> int:
        """Get total messages processed"""
        return self._message_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            "running": self._running,
            "messages_processed": self._message_count,
            "buffer_size": len(self.message_buffer),
            "buffer_max": self.message_buffer.maxlen,
            "config": {
                "enabled": self.kafka_config.enabled,
                "bootstrap_servers": self.kafka_config.bootstrap_servers,
                "topic": self.kafka_config.topic,
                "group_id": self.kafka_config.group_id
            }
        }
