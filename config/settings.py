"""
Centralized configuration management using Pydantic BaseSettings
Provides type-safe, validated configuration with sensible defaults
"""

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import warnings
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


class RedisSettings(BaseModel):
    """Redis cache configuration with string-to-bool parsing"""
    enabled: bool = Field(default=True, description="Enable Redis caching")
    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, ge=1, le=65535, description="Redis port")
    db: int = Field(default=0, ge=0, le=15, description="Redis database number")

    @field_validator('enabled', mode='before')
    @classmethod
    def parse_enabled(cls, v):
        """Parse string 'true'/'false' to boolean (fixes fragile string parsing issue)"""
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return bool(v)

    @field_validator('port')
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port range"""
        if not (1 <= v <= 65535):
            raise ValueError(f"Redis port must be between 1-65535, got {v}")
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
        env_nested_delimiter='_',  # Support POSTGRES_HOST → database.host
        extra='ignore'  # Ignore unknown env vars
    )

    # Nested settings with env mapping
    database: DatabaseSettings = Field(
        default_factory=DatabaseSettings,
        description="PostgreSQL database settings"
    )
    redis: RedisSettings = Field(
        default_factory=RedisSettings,
        description="Redis cache settings"
    )
    kafka: KafkaSettings = Field(
        default_factory=KafkaSettings,
        description="Kafka messaging settings"
    )
    api: APISettings = Field(
        default_factory=APISettings,
        description="API server settings"
    )
    logging: LoggingSettings = Field(
        default_factory=LoggingSettings,
        description="Logging settings"
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

        # Redis config
        status = "ENABLED" if self.redis.enabled else "DISABLED"
        logger.info(f"Redis: {status} ({self.redis.host}:{self.redis.port})")
        if not self.redis.enabled:
            logger.warning("⚠️  Redis caching disabled - Performance may be reduced")

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

