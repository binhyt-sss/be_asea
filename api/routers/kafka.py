"""
Kafka Streaming Endpoints
WebSocket for real-time alerts and recent messages API
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Set, Optional
from loguru import logger
import asyncio

from api.dependencies import get_message_buffer

router = APIRouter(prefix="/kafka", tags=["Kafka Streaming"])

# Active WebSocket connections
active_connections: Set[WebSocket] = set()


async def broadcast_message(message: dict):
    """
    Broadcast message to all active WebSocket connections
    
    Args:
        message: Message to broadcast
    """
    if not active_connections:
        return
    
    disconnected = set()
    
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send to WebSocket: {e}")
            disconnected.add(connection)
    
    # Remove disconnected clients
    for conn in disconnected:
        active_connections.discard(conn)


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """
    WebSocket endpoint for real-time Kafka alerts
    
    Features:
    - Automatic reconnection support
    - Sends recent messages on connect
    - Real-time message streaming
    - Heartbeat for connection health
    """
    await websocket.accept()
    active_connections.add(websocket)
    
    client_info = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "unknown"
    logger.info(f"🔌 WebSocket connected: {client_info} (total: {len(active_connections)})")
    
    message_buffer = get_message_buffer()
    
    try:
        # Send recent messages on connect
        recent_messages = list(message_buffer)[-10:]
        if recent_messages:
            await websocket.send_json({
                "type": "history",
                "count": len(recent_messages),
                "messages": recent_messages
            })
        
        # Send welcome message
        await websocket.send_json({
            "type": "system",
            "message": "Connected to Kafka alert stream",
            "buffer_size": len(message_buffer),
            "client": client_info
        })
        
        # Track last sent index
        last_sent = len(message_buffer)
        
        # Keep connection alive and send new messages
        while True:
            # Check for new messages
            current_size = len(message_buffer)
            if current_size > last_sent:
                new_messages = list(message_buffer)[last_sent:]
                for msg in new_messages:
                    await websocket.send_json({
                        "type": "alert",
                        "data": msg
                    })
                last_sent = current_size
            
            # Small sleep to prevent CPU spinning
            await asyncio.sleep(0.1)
            
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected: {client_info}")
    except Exception as e:
        logger.error(f"❌ WebSocket error ({client_info}): {e}")
    finally:
        active_connections.discard(websocket)
        logger.info(f"👋 WebSocket removed: {client_info} (remaining: {len(active_connections)})")


@router.get("/messages/recent")
async def get_recent_messages(
    limit: int = Query(default=50, ge=1, le=1000, description="Number of recent messages to retrieve")
):
    """
    Get recent Kafka messages from buffer
    
    Args:
        limit: Maximum number of messages (1-1000)
    
    Returns:
        Recent messages with metadata
    """
    message_buffer = get_message_buffer()
    messages = list(message_buffer)[-limit:]
    
    return {
        "count": len(messages),
        "limit": limit,
        "buffer_size": len(message_buffer),
        "buffer_max": message_buffer.maxlen,
        "messages": messages
    }


@router.get("/stats")
async def get_kafka_stats():
    """
    Get Kafka streaming statistics
    
    Returns:
        Service statistics and connection info
    """
    message_buffer = get_message_buffer()
    
    return {
        "websocket": {
            "active_connections": len(active_connections),
            "clients": [
                f"{ws.client.host}:{ws.client.port}" if ws.client else "unknown"
                for ws in active_connections
            ]
        },
        "buffer": {
            "current_size": len(message_buffer),
            "max_size": message_buffer.maxlen,
            "usage_percent": round(len(message_buffer) / message_buffer.maxlen * 100, 2)
        }
    }


@router.post("/broadcast")
async def broadcast_test_message(message: dict):
    """
    Test endpoint to broadcast a message to all connected clients
    
    Args:
        message: Message to broadcast
    
    Returns:
        Broadcast status
    """
    await broadcast_message(message)
    
    return {
        "status": "broadcasted",
        "recipients": len(active_connections),
        "message": message
    }
