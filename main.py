"""
Person ReID Backend - Unified API
Combines Database API and Kafka Consumer API into a single application
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from loguru import logger

# Database imports
from database.session import get_db, init_db, close_db
from database import models as db_models
from schemas import database as schemas
from crud import user_crud, zone_crud
from utils.redis_cache import RedisCache
from config import get_settings

# Kafka imports
from utils.kafka_manager import KafkaAlertConsumer
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
from collections import deque

# Create unified app
app = FastAPI(
    title="Person ReID Backend - Unified API",
    version="2.0.0",
    description="Async SQLAlchemy + Kafka Consumer in a single service"
)

settings = get_settings()
redis_cache = RedisCache(redis_config=settings.redis)

# Kafka consumer for WebSocket
kafka_consumer = None
message_buffer = deque(maxlen=100)
consumer_thread = None


@app.on_event("startup")
async def startup_event():
    global kafka_consumer, consumer_thread
    
    logger.info("🚀 Starting Unified Backend Service...")
    
    # Initialize database
    await init_db()
    logger.info("✅ Database initialized")
    
    # Initialize Kafka consumer
    if settings.kafka.enabled:
        try:
            kafka_consumer = KafkaAlertConsumer(kafka_config=settings.kafka)
            
            def message_handler(message: dict):
                """Callback to handle incoming Kafka messages"""
                message_buffer.append(message)
            
            def consume_messages():
                """Thread function to consume Kafka messages"""
                kafka_consumer.consume(callback=message_handler, timeout=1.0)
            
            import threading
            consumer_thread = threading.Thread(target=consume_messages, daemon=True)
            consumer_thread.start()
            logger.info("✅ Kafka consumer started")
        except Exception as e:
            logger.warning(f"⚠️  Kafka consumer failed to start: {e}")
    
    logger.info("✅ Unified Backend Service ready")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Unified Backend Service...")
    await redis_cache.close()
    await close_db()
    if kafka_consumer:
        kafka_consumer.close()


@app.get("/")
async def root():
    return {
        "service": "Person ReID Unified Backend",
        "version": "2.0.0",
        "endpoints": {
            "database": "/users, /zones, /stats",
            "kafka": "/ws/alerts, /messages/recent",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    redis_stats = await redis_cache.get_stats() if redis_cache.is_available() else {"enabled": False}
    return {
        "status": "healthy",
        "service": "unified_backend",
        "version": "2.0.0",
        "database": "PostgreSQL + asyncpg",
        "orm": "SQLAlchemy 2.0 async",
        "kafka_enabled": settings.kafka.enabled,
        "kafka_running": kafka_consumer is not None,
        "messages_received": len(message_buffer),
        "redis": redis_stats
    }


# ============================================================================
# USER ENDPOINTS
# ============================================================================

@app.get("/users", response_model=List[schemas.User])
async def get_all_users(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    users = await user_crud.get_all_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await user_crud.get_user_by_id(db, user_id)
    if user is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.post("/users", response_model=schemas.User)
async def create_user(user_data: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    from fastapi import HTTPException
    existing_user = await user_crud.get_user_by_global_id(db, user_data.global_id)
    if existing_user:
        raise HTTPException(status_code=400, detail=f"User with global_id {user_data.global_id} already exists")
    
    user = await user_crud.create_user(db, user_data)
    await redis_cache.invalidate_users_dict()
    return user


@app.put("/users/{user_id}", response_model=schemas.User)
async def update_user(user_id: int, user_data: schemas.UserUpdate, db: AsyncSession = Depends(get_db)):
    from fastapi import HTTPException
    user = await user_crud.update_user(db, user_id, user_data)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    await redis_cache.invalidate_users_dict()
    return user


@app.delete("/users/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    from fastapi import HTTPException
    success = await user_crud.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    await redis_cache.invalidate_users_dict()
    return JSONResponse(content={"message": f"User {user_id} deleted successfully"})


@app.get("/users-dict")
async def get_users_dict(use_cache: bool = True, db: AsyncSession = Depends(get_db)):
    if use_cache and redis_cache.is_available():
        cached_dict = await redis_cache.get_users_dict()
        if cached_dict:
            return cached_dict
    
    users_dict = await user_crud.get_users_dict(db)
    if redis_cache.is_available():
        await redis_cache.cache_users_dict(users_dict, ttl=3600)
    return users_dict


# ============================================================================
# ZONE ENDPOINTS
# ============================================================================

@app.get("/zones", response_model=List[schemas.WorkingZone])
async def get_all_zones(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    zones = await zone_crud.get_all_zones(db, skip=skip, limit=limit)
    return zones


@app.get("/zones/{zone_id}", response_model=schemas.WorkingZone)
async def get_zone(zone_id: str, db: AsyncSession = Depends(get_db)):
    from fastapi import HTTPException
    zone = await zone_crud.get_zone_by_id(db, zone_id)
    if zone is None:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone


@app.post("/zones", response_model=schemas.WorkingZone)
async def create_zone(zone_data: schemas.WorkingZoneCreate, db: AsyncSession = Depends(get_db)):
    from fastapi import HTTPException
    existing_zone = await zone_crud.get_zone_by_id(db, zone_data.zone_id)
    if existing_zone:
        raise HTTPException(status_code=400, detail=f"Zone with zone_id {zone_data.zone_id} already exists")
    
    zone = await zone_crud.create_zone(db, zone_data)
    return zone


# ============================================================================
# STATISTICS ENDPOINTS
# ============================================================================

@app.get("/stats/users")
async def get_user_stats(db: AsyncSession = Depends(get_db)):
    total_users = await user_crud.count_users(db)
    return {"total_users": total_users}


@app.get("/stats/zones")
async def get_zone_stats(db: AsyncSession = Depends(get_db)):
    total_zones = await zone_crud.count_zones(db)
    zones_with_counts = await zone_crud.get_zones_with_user_counts(db)
    return {"total_zones": total_zones, "zones": zones_with_counts}


# ============================================================================
# KAFKA WEBSOCKET ENDPOINT
# ============================================================================

@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    await websocket.accept()
    logger.info(f"WebSocket client connected from {websocket.client}")
    
    try:
        last_sent_index = 0
        
        while True:
            if len(message_buffer) > last_sent_index:
                new_messages = list(message_buffer)[last_sent_index:]
                for msg in new_messages:
                    await websocket.send_json(msg)
                last_sent_index = len(message_buffer)
            
            await asyncio.sleep(0.1)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected from {websocket.client}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


@app.get("/messages/recent")
async def get_recent_messages(limit: int = 50):
    messages = list(message_buffer)[-limit:]
    return {"count": len(messages), "messages": messages}


# ============================================================================
# CACHE MANAGEMENT
# ============================================================================

@app.get("/cache/stats")
async def get_cache_stats():
    return await redis_cache.get_stats()


@app.post("/cache/invalidate/users-dict")
async def invalidate_users_cache():
    success = await redis_cache.invalidate_users_dict()
    return {"message": "Users dict cache invalidated" if success else "Redis not available"}


if __name__ == "__main__":
    import uvicorn
    
    print("="*70)
    print("🚀 Starting Unified Person ReID Backend")
    print("="*70)
    print("\n📊 Unified API:  http://localhost:8000")
    print("   Swagger UI:   http://localhost:8000/docs")
    print("   ReDoc:        http://localhost:8000/redoc")
    print("\n💡 All endpoints on single port:")
    print("   • Database:   /users, /zones, /stats")
    print("   • Kafka:      /ws/alerts, /messages/recent")
    print("   • Health:     /health")
    print("\n" + "="*70 + "\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


