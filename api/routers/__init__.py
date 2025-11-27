"""
API Routers
Modular endpoint organization for clean architecture
"""

from .users import router as users_router
from .zones import router as zones_router
from .stats import router as stats_router
from .kafka import router as kafka_router
from .cache import router as cache_router

__all__ = [
    "users_router",
    "zones_router", 
    "stats_router",
    "kafka_router",
    "cache_router"
]
