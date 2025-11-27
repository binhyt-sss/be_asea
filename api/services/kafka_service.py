"""
Kafka Background Service
Manages Kafka consumer in background thread
"""

import threading
from typing import Optional
from collections import deque
from loguru import logger

from utils.kafka_manager import KafkaAlertConsumer
from config import KafkaSettings


class KafkaService:
    """
    Kafka consumer service running in background thread
    
    Features:
    - Background message consumption
    - Thread-safe message buffer
    - Graceful shutdown
    """
    
    def __init__(self, kafka_config: KafkaSettings, message_buffer: deque):
        """
        Initialize Kafka service
        
        Args:
            kafka_config: Kafka configuration
            message_buffer: Shared message buffer for storing messages
        """
        self.kafka_config = kafka_config
        self.message_buffer = message_buffer
        self.consumer: Optional[KafkaAlertConsumer] = None
        self.consumer_thread: Optional[threading.Thread] = None
        self._running = False
    
    def start(self):
        """Start Kafka consumer in background thread"""
        if not self.kafka_config.enabled:
            logger.info("⚠️  Kafka is disabled in configuration")
            return
        
        try:
            self.consumer = KafkaAlertConsumer(kafka_config=self.kafka_config)
            
            def message_handler(message: dict):
                """Callback to handle incoming Kafka messages"""
                self.message_buffer.append(message)
            
            def consume_messages():
                """Thread function to consume Kafka messages"""
                self._running = True
                while self._running:
                    try:
                        self.consumer.consume(callback=message_handler, timeout=1.0)
                    except Exception as e:
                        logger.error(f"Kafka consume error: {e}")
                        if self._running:  # Only log if not shutting down
                            continue
                        break
            
            self.consumer_thread = threading.Thread(
                target=consume_messages, 
                daemon=True,
                name="KafkaConsumerThread"
            )
            self.consumer_thread.start()
            logger.info("✅ Kafka consumer started")
            
        except Exception as e:
            logger.warning(f"⚠️  Kafka consumer failed to start: {e}")
    
    def stop(self):
        """Stop Kafka consumer gracefully"""
        if not self._running:
            return
        
        logger.info("Stopping Kafka consumer...")
        self._running = False
        
        if self.consumer:
            try:
                self.consumer.close()
                logger.info("✅ Kafka consumer closed")
            except Exception as e:
                logger.error(f"Error closing Kafka consumer: {e}")
        
        if self.consumer_thread and self.consumer_thread.is_alive():
            self.consumer_thread.join(timeout=5)
            logger.info("✅ Kafka consumer thread stopped")
    
    def is_running(self) -> bool:
        """Check if Kafka consumer is running"""
        return self._running and self.consumer is not None
