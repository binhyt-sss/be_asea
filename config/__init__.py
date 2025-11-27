"""
Configuration management for person-reid-backend.

Usage:
    from config import get_settings

    settings = get_settings()
    print(settings.database.host)
    print(settings.redis.enabled)
"""

from .settings import (
    Settings,
    DatabaseSettings,
    RedisSettings,
    KafkaSettings,
    APISettings,
    LoggingSettings,
    get_settings,
    reset_settings
)

__all__ = [
    'Settings',
    'DatabaseSettings',
    'RedisSettings',
    'KafkaSettings',
    'APISettings',
    'LoggingSettings',
    'get_settings',
    'reset_settings',
]

