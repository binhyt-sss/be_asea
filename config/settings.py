"""
Centralized configuration management using Pydantic BaseSettings
Provides type-safe, validated configuration with sensible defaults
"""

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import warnings
import json
from loguru import logger


class DatabaseSettings(BaseModel):
    """PostgreSQL database configuration with validation"""
    host: str = Field(default="localhost", description="PostgreSQL host")
    port: int = Field(default=5432, ge=1, le=65535, description="PostgreSQL port")
    user: str = Field(default="hailt", description="PostgreSQL username")
    password: str = Field(default="1", description="PostgreSQL password")
    database: str = Field(default="hailt_imespro", description="Database name")
    table: str = Field(default="user", description="User table name")

    @field_validator('password')
    @classmethod
    def warn_weak_password(cls, v: str) -> str:
        """Warn about weak passwords but allow for dev/testing"""
        if len(v) <= 2:
            msg = (
                f"⚠️  Weak PostgreSQL password detected (length={len(v)}). "
                "This is acceptable for development but MUST be changed for production!"
            )
            warnings.warn(msg, UserWarning, stacklevel=2)
            logger.warning("⚠️  Using weak database password - OK for dev, NOT for production")
        return v

    @field_validator('port')
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port range"""
        if not (1 <= v <= 65535):
            raise ValueError(f"Port must be between 1-65535, got {v}")
        return v


class KafkaSettings(BaseModel):
    """Kafka messaging configuration (fixes hardcoded values issue)"""
    enabled: bool = Field(default=True, description="Enable Kafka messaging")
    bootstrap_servers: str = Field(default="localhost:9092", description="Kafka broker address")
    topic: str = Field(default="person_reid_alerts", description="Kafka topic name")
    group_id: str = Field(default="person_reid_ui_consumers", description="Consumer group ID")

    @field_validator('enabled', mode='before')
    @classmethod
    def parse_enabled(cls, v):
        """Parse string 'true'/'false' to boolean"""
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return bool(v)

    @field_validator('bootstrap_servers')
    @classmethod
    def validate_bootstrap_servers(cls, v: str) -> str:
        """Warn if Kafka server format seems incorrect"""
        if ':' not in v:
            msg = f"⚠️  Kafka bootstrap_servers '{v}' missing port. Expected format: 'host:port'"
            warnings.warn(msg, UserWarning, stacklevel=2)
            logger.warning(msg)
        return v


class APISettings(BaseModel):
    """API server configuration"""
    host: str = Field(default="0.0.0.0", description="API bind host")
    database_api_port: int = Field(default=8001, ge=1024, le=65535, description="Database API port")
    kafka_api_port: int = Field(default=8004, ge=1024, le=65535, description="Kafka API port")

    @field_validator('database_api_port', 'kafka_api_port')
    @classmethod
    def validate_port_range(cls, v: int, info) -> int:
        """Warn if using privileged ports"""
        if v < 1024:
            msg = f"⚠️  {info.field_name} using privileged port {v}. Consider ports >= 1024"
            warnings.warn(msg, UserWarning, stacklevel=2)
            logger.warning(msg)
        return v


class LoggingSettings(BaseModel):
    """Logging configuration"""
    level: str = Field(default="INFO", description="Log level")

    @field_validator('level')
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate and normalize log level"""
        v = v.upper()
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v not in valid_levels:
            msg = f"⚠️  Invalid log level '{v}'. Using 'INFO'. Valid: {valid_levels}"
            warnings.warn(msg, UserWarning, stacklevel=2)
            logger.warning(msg)
            return 'INFO'
        return v


class Settings(BaseSettings):
    """
    Application configuration loaded from .env file with validation.

    Features:
    - Single source of truth for all configuration
    - Type-safe with Pydantic validation
    - Warning system for weak configs (doesn't crash)
    - Sensible defaults for development
    - Environment variable override support

    Example:
        settings = get_settings()
        db_host = settings.database.host
        redis_enabled = settings.redis.enabled
    """

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        env_prefix='',  # No global prefix
        extra='ignore'  # Ignore unknown env vars
    )

    # Direct env var mapping for flat structure
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_user: str = Field(default="hailt", alias="POSTGRES_USER")
    postgres_password: str = Field(default="1", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="hailt_imespro", alias="POSTGRES_DB")
    postgres_table: str = Field(default="user", alias="POSTGRES_TABLE")

    kafka_enabled: bool = Field(default=True, alias="KAFKA_ENABLED")
    kafka_bootstrap_servers: str = Field(default="localhost:9092", alias="KAFKA_BOOTSTRAP_SERVERS")
    kafka_topic: str = Field(default="person_reid_alerts", alias="KAFKA_TOPIC")
    kafka_group_id: str = Field(default="person_reid_ui_consumers", alias="KAFKA_GROUP_ID")

    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_database_api_port: int = Field(default=8001, alias="API_DATABASE_API_PORT")
    api_kafka_api_port: int = Field(default=8004, alias="API_KAFKA_API_PORT")

    logging_level: str = Field(default="INFO", alias="LOGGING_LEVEL")

    # Consumer configuration (NEW)
    consumer_type: str = Field(default="kafka", alias="CONSUMER_TYPE")

    # SSE config (NEW)
    sse_enabled: bool = Field(default=False, alias="SSE_ENABLED")
    sse_url: str = Field(default="http://localhost:8000/events/alerts", alias="SSE_URL")
    sse_headers: str = Field(default="{}", alias="SSE_HEADERS")  # JSON string
    sse_retry_delay: int = Field(default=5, alias="SSE_RETRY_DELAY")
    sse_max_retries: int = Field(default=-1, alias="SSE_MAX_RETRIES")

    # WebSocket upstream config (NEW)
    websocket_enabled: bool = Field(default=False, alias="WEBSOCKET_ENABLED")
    websocket_url: str = Field(default="ws://localhost:8000/ws/alerts", alias="WEBSOCKET_URL")
    websocket_reconnect_delay: int = Field(default=5, alias="WEBSOCKET_RECONNECT_DELAY")
    websocket_ping_interval: int = Field(default=20, alias="WEBSOCKET_PING_INTERVAL")
    websocket_ping_timeout: int = Field(default=10, alias="WEBSOCKET_PING_TIMEOUT")

    @property
    def database(self) -> DatabaseSettings:
        """Build DatabaseSettings from flat env vars"""
        return DatabaseSettings(
            host=self.postgres_host,
            port=self.postgres_port,
            user=self.postgres_user,
            password=self.postgres_password,
            database=self.postgres_db,
            table=self.postgres_table
        )

    @property
    def kafka(self) -> KafkaSettings:
        """Build KafkaSettings from flat env vars"""
        return KafkaSettings(
            enabled=self.kafka_enabled,
            bootstrap_servers=self.kafka_bootstrap_servers,
            topic=self.kafka_topic,
            group_id=self.kafka_group_id
        )

    @property
    def api(self) -> APISettings:
        """Build APISettings from flat env vars"""
        return APISettings(
            host=self.api_host,
            database_api_port=self.api_database_api_port,
            kafka_api_port=self.api_kafka_api_port
        )

    @property
    def logging(self) -> LoggingSettings:
        """Build LoggingSettings from flat env vars"""
        return LoggingSettings(level=self.logging_level)

    @property
    def consumer(self):
        """Build ConsumerSettings from flat env vars"""
        from config.consumer_config import (
            ConsumerSettings,
            KafkaConsumerConfig,
            SSEConsumerConfig,
            WebSocketConsumerConfig
        )

        # Parse SSE headers from JSON string
        sse_headers = {}
        if self.sse_headers:
            try:
                sse_headers = json.loads(self.sse_headers)
            except json.JSONDecodeError:
                logger.warning("⚠️  Invalid SSE_HEADERS JSON, using empty dict")

        return ConsumerSettings(
            consumer_type=self.consumer_type,
            kafka=KafkaConsumerConfig(
                enabled=self.kafka_enabled,
                bootstrap_servers=self.kafka_bootstrap_servers,
                topic=self.kafka_topic,
                group_id=self.kafka_group_id
            ),
            sse=SSEConsumerConfig(
                enabled=self.sse_enabled,
                url=self.sse_url,
                headers=sse_headers,
                retry_delay=self.sse_retry_delay,
                max_retries=self.sse_max_retries
            ),
            websocket=WebSocketConsumerConfig(
                enabled=self.websocket_enabled,
                url=self.websocket_url,
                reconnect_delay=self.websocket_reconnect_delay,
                ping_interval=self.websocket_ping_interval,
                ping_timeout=self.websocket_ping_timeout
            )
        )

    def model_post_init(self, __context) -> None:
        """Log configuration status after initialization"""
        self._log_configuration_status()

    def _log_configuration_status(self):
        """Log configuration status and warnings on startup"""
        logger.info("=" * 60)
        logger.info("Configuration Loaded Successfully")
        logger.info("=" * 60)

        # Database config
        logger.info(f"Database: {self.database.host}:{self.database.port}/{self.database.database}")
        if self.database.password in ['1', 'password', 'admin', 'root']:
            logger.warning("⚠️  WEAK DATABASE PASSWORD - Change for production!")

        # Kafka config
        status = "ENABLED" if self.kafka.enabled else "DISABLED"
        logger.info(f"Kafka: {status} ({self.kafka.bootstrap_servers})")
        if not self.kafka.enabled:
            logger.warning("⚠️  Kafka alerts disabled - No real-time notifications")

        # API config
        logger.info(f"API Ports: Database={self.api.database_api_port}, Kafka={self.api.kafka_api_port}")
        logger.info(f"Log Level: {self.logging.level}")
        logger.info("=" * 60)


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get or create Settings singleton.
    Loads from .env on first call, returns cached instance on subsequent calls.

    Returns:
        Settings instance

    Example:
        from config import get_settings

        settings = get_settings()
        print(settings.database.host)
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings():
    """
    Reset settings singleton (useful for testing).

    Example:
        reset_settings()
        settings = get_settings()  # Will reload from .env
    """
    global _settings
    _settings = None

