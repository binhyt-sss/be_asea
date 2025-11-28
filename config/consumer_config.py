"""
Consumer Configuration Models
Pydantic models for all consumer types with validation
"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any
import warnings
from loguru import logger


class KafkaConsumerConfig(BaseModel):
    """Kafka consumer configuration"""
    enabled: bool = Field(default=True, description="Enable Kafka consumer")
    bootstrap_servers: str = Field(default="localhost:9092", description="Kafka broker address")
    topic: str = Field(default="person_reid_alerts", description="Kafka topic name")
    group_id: str = Field(default="person_reid_ui_consumers", description="Consumer group ID")

    @field_validator('bootstrap_servers')
    @classmethod
    def validate_bootstrap_servers(cls, v: str) -> str:
        """Warn if Kafka server format seems incorrect"""
        if ':' not in v:
            msg = f"⚠️  Kafka bootstrap_servers '{v}' missing port. Expected format: 'host:port'"
            warnings.warn(msg, UserWarning, stacklevel=2)
            logger.warning(msg)
        return v


class SSEConsumerConfig(BaseModel):
    """Server-Sent Events consumer configuration"""
    enabled: bool = Field(default=False, description="Enable SSE consumer")
    url: str = Field(default="http://localhost:8000/events/alerts", description="SSE endpoint URL")
    headers: Dict[str, str] = Field(default_factory=dict, description="HTTP headers for SSE connection")
    retry_delay: int = Field(default=5, ge=1, le=300, description="Seconds to wait before retry on disconnect")
    max_retries: int = Field(default=-1, description="Max reconnection attempts (-1 for unlimited)")

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate SSE URL format"""
        if not v.startswith('http://') and not v.startswith('https://'):
            raise ValueError("SSE url must start with http:// or https://")
        return v

    @field_validator('retry_delay')
    @classmethod
    def validate_retry_delay(cls, v: int) -> int:
        """Validate retry delay range"""
        if v < 1 or v > 300:
            raise ValueError(f"retry_delay must be between 1-300 seconds, got {v}")
        return v


class WebSocketConsumerConfig(BaseModel):
    """WebSocket consumer configuration"""
    enabled: bool = Field(default=False, description="Enable WebSocket consumer")
    url: str = Field(default="ws://localhost:8000/ws/alerts", description="WebSocket URL")
    headers: Dict[str, str] = Field(default_factory=dict, description="WebSocket connection headers")
    reconnect_delay: int = Field(default=5, ge=1, le=300, description="Seconds to wait before reconnect")
    ping_interval: int = Field(default=20, ge=5, le=120, description="WebSocket ping interval in seconds")
    ping_timeout: int = Field(default=10, ge=5, le=60, description="WebSocket ping timeout in seconds")

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate WebSocket URL format"""
        if not v.startswith('ws://') and not v.startswith('wss://'):
            raise ValueError("WebSocket url must start with ws:// or wss://")
        return v


class ConsumerSettings(BaseModel):
    """
    Top-level consumer configuration
    Determines which consumer to use at runtime
    """

    # Consumer type selection
    consumer_type: str = Field(
        default="kafka",
        description="Type of consumer to use: kafka, sse, websocket"
    )

    # Individual consumer configurations
    kafka: KafkaConsumerConfig = Field(default_factory=KafkaConsumerConfig)
    sse: SSEConsumerConfig = Field(default_factory=SSEConsumerConfig)
    websocket: WebSocketConsumerConfig = Field(default_factory=WebSocketConsumerConfig)

    @field_validator('consumer_type')
    @classmethod
    def validate_consumer_type(cls, v: str) -> str:
        """Validate consumer type"""
        v = v.lower()
        valid_types = ['kafka', 'sse', 'websocket']
        if v not in valid_types:
            msg = f"Invalid consumer_type '{v}'. Valid options: {valid_types}"
            raise ValueError(msg)
        return v

    def get_active_config(self) -> Any:
        """
        Get configuration for the active consumer type

        Returns:
            KafkaConsumerConfig | SSEConsumerConfig | WebSocketConsumerConfig

        Raises:
            ValueError: If consumer type is unknown
        """
        if self.consumer_type == 'kafka':
            return self.kafka
        elif self.consumer_type == 'sse':
            return self.sse
        elif self.consumer_type == 'websocket':
            return self.websocket
        else:
            raise ValueError(f"Unknown consumer type: {self.consumer_type}")

    def model_post_init(self, __context) -> None:
        """Log configuration after initialization"""
        logger.info(f"📡 Consumer type selected: {self.consumer_type.upper()}")
        active_config = self.get_active_config()
        if hasattr(active_config, 'enabled') and not active_config.enabled:
            logger.warning(f"⚠️  {self.consumer_type.upper()} consumer is DISABLED in configuration")
