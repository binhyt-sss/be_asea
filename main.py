"""
Person ReID Backend - Unified API
Modular FastAPI application with async architecture
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

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

# Services
from api.services import KafkaService
from api.dependencies import get_message_buffer

# Create unified app
app = FastAPI(
    title="Person ReID Backend - Unified API",
    version="2.0.0",
    description="Async SQLAlchemy + Kafka in modular architecture"
)

# Global service instances
settings = get_settings()
kafka_service: KafkaService = None


@app.on_event("startup")
async def startup_event():
    """Initialize all services on startup"""
    global kafka_service
    
    logger.info("🚀 Starting Unified Backend Service...")
    
    # Initialize database
    await init_db()
    logger.info("✅ Database initialized")
    
    # Start Kafka consumer in background
    kafka_service = KafkaService(
        kafka_config=settings.kafka,
        message_buffer=get_message_buffer()
    )
    kafka_service.start()
    
    logger.info("✅ Unified Backend Service ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Gracefully shutdown all services"""
    logger.info("Shutting down Unified Backend Service...")

    # Close database
    await close_db()

    # Stop Kafka consumer
    if kafka_service:
        kafka_service.stop()

    logger.info("✅ Shutdown complete")


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
    """Health check with service status"""
    message_buffer = get_message_buffer()

    return {
        "status": "healthy",
        "service": "unified_backend",
        "version": "2.0.0",
        "database": "PostgreSQL + asyncpg",
        "orm": "SQLAlchemy 2.0 async",
        "kafka_enabled": settings.kafka.enabled,
        "kafka_running": kafka_service.is_running() if kafka_service else False,
        "messages_received": len(message_buffer)
    }




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

