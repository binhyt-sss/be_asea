"""
Person ReID Backend - Unified API
Modular FastAPI application with async architecture
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from loguru import logger

# Core imports
from database.session import init_db, close_db
from config import get_settings

# Routers
from api.routers import (
    users_router,
    zones_router,
    stats_router,
    kafka_router
)
from api.routers.kafka import broadcast_message

# Services
from api.services import KafkaService  # Legacy - kept for backward compatibility
from api.services.consumer_factory import ConsumerFactory
from api.dependencies import get_message_buffer

# Global service instances
settings = get_settings()
kafka_service = None  # Will hold the consumer service (kept name for compatibility)
consumer_service = None  # Alias for clarity


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager (modern FastAPI pattern)
    Replaces deprecated @app.on_event("startup"/"shutdown")
    """
    global kafka_service, consumer_service

    # Startup
    logger.info("🚀 Starting Unified Backend Service...")

    # Initialize database
    await init_db()
    logger.info("✅ Database initialized")

    # Create consumer service using factory (NEW - supports multiple consumer types)
    consumer_service = ConsumerFactory.create(
        consumer_settings=settings.consumer,
        message_buffer=get_message_buffer(),
        broadcast_callback=broadcast_message  # Link to WebSocket broadcaster
    )
    await consumer_service.start()

    # Keep kafka_service reference for backward compatibility
    kafka_service = consumer_service

    logger.info("✅ Unified Backend Service ready")

    yield  # Application is running

    # Shutdown
    logger.info("Shutting down Unified Backend Service...")

    # Stop consumer service
    if consumer_service:
        await consumer_service.stop()

    # Close database
    await close_db()

    logger.info("✅ Shutdown complete")


# Create unified app with lifespan
app = FastAPI(
    title="Person ReID Backend - Unified API",
    version="2.0.0",
    description="Async SQLAlchemy + Kafka in modular architecture",
    lifespan=lifespan
)


# Register routers
app.include_router(users_router)
app.include_router(zones_router)
app.include_router(stats_router)
app.include_router(kafka_router)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Person ReID Unified Backend",
        "version": "2.0.0",
        "architecture": "Async SQLAlchemy + Kafka",
        "endpoints": {
            "database": "/users, /zones, /stats",
            "kafka": "/ws/alerts, /messages/recent",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint

    Returns:
        Service health status and statistics
    """
    message_buffer = get_message_buffer()

    health = {
        "status": "healthy",
        "service": "unified_backend",
        "version": "2.0.0",
        "database": "PostgreSQL + asyncpg",
        "orm": "SQLAlchemy 2.0 async",
        "consumer": {
            "type": settings.consumer.consumer_type,
            "running": consumer_service.is_running() if consumer_service else False,
            "messages_received": consumer_service.get_message_count() if consumer_service else 0
        },
        "buffer": {
            "size": len(message_buffer),
            "max": message_buffer.maxlen
        }
    }

    # Add detailed consumer stats if running
    if consumer_service and consumer_service.is_running():
        health["consumer_stats"] = consumer_service.get_stats()

    return health




if __name__ == "__main__":
    import uvicorn
    
    print("="*70)
    print("🚀 Starting Unified Person ReID Backend")
    print("="*70)
    print("\n📊 Unified API:  http://localhost:8000")
    print("   Swagger UI:   http://localhost:8000/docs")
    print("   ReDoc:        http://localhost:8000/redoc")
    print("\n💡 Modular Architecture:")
    print("   • Users:      /users (CRUD)")
    print("   • Zones:      /zones (CRUD)")
    print("   • Stats:      /stats (aggregates)")
    print("   • Kafka:      /ws/alerts, /messages/recent")
    print("   • Health:     /health")
    print("\n" + "="*70 + "\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

