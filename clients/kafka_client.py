"""
Kafka Message Client
Adapter for Kafka consumer using existing KafkaAlertConsumer
"""

from typing import Dict, Any, Optional
from loguru import logger

from clients.base import MessageClient, MessageHandler
from utils.kafka_manager import KafkaAlertConsumer
from config import get_settings


class KafkaMessageClient(MessageClient):
    """
    Kafka message client implementation
    
    Example:
        # Using default config from settings
        client = KafkaMessageClient()
        client.connect()
        
        def handler(msg):
            print(f"User: {msg['user_name']}, Zone: {msg['zone_name']}")
        
        client.consume(handler, timeout=1.0)
        client.close()
        
        # Using custom config
        client = KafkaMessageClient({
            'bootstrap_servers': 'kafka:9092',
            'topic': 'my_topic',
            'group_id': 'my_group'
        })
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Kafka client
        
        Args:
            config: Optional Kafka configuration
                - bootstrap_servers: Kafka broker address
                - topic: Topic to consume from
                - group_id: Consumer group ID
                If not provided, uses settings from config
        """
        super().__init__(config)
        
        # Use provided config or load from settings
        if not config:
            settings = get_settings()
            self.config = {
                'bootstrap_servers': settings.kafka.bootstrap_servers,
                'topic': settings.kafka.topic,
                'group_id': settings.kafka.group_id
            }
        
        self.consumer: Optional[KafkaAlertConsumer] = None
    
    def connect(self):
        """Connect to Kafka broker"""
        try:
            from config import KafkaSettings
            
            # Create KafkaSettings from config dict
            kafka_settings = KafkaSettings(
                enabled=True,
                bootstrap_servers=self.config['bootstrap_servers'],
                topic=self.config['topic'],
                group_id=self.config['group_id']
            )
            
            self.consumer = KafkaAlertConsumer(kafka_config=kafka_settings)
            self.connected = True
            logger.info(f"✅ Connected to Kafka: {self.config['bootstrap_servers']}")
            logger.info(f"📨 Consuming topic: {self.config['topic']}")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Kafka: {e}")
            raise ConnectionError(f"Kafka connection failed: {e}")
    
    def consume(self, handler: MessageHandler, timeout: Optional[float] = None):
        """
        Consume messages from Kafka
        
        Args:
            handler: Callback to process each message
            timeout: Poll timeout in seconds (default: 1.0)
        """
        if not self.connected or not self.consumer:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        timeout = timeout or 1.0
        
        try:
            def wrapped_handler(message: Dict[str, Any]):
                """Wrapper to track message count"""
                self._increment_message_count()
                handler(message)
            
            self.consumer.consume(callback=wrapped_handler, timeout=timeout)
            
        except Exception as e:
            logger.error(f"Error consuming Kafka message: {e}")
            raise
    
    def close(self):
        """Close Kafka consumer"""
        if self.consumer:
            try:
                self.consumer.close()
                self.connected = False
                logger.info(f"✅ Kafka client closed ({self._message_count} messages processed)")
            except Exception as e:
                logger.error(f"Error closing Kafka consumer: {e}")
