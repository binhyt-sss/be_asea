"""
Kafka Streaming Endpoints
WebSocket for real-time alerts and recent messages
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
import asyncio

from api.dependencies import get_message_buffer

router = APIRouter(tags=["Kafka"])


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """WebSocket endpoint for real-time Kafka alerts"""
    await websocket.accept()
    logger.info(f"WebSocket client connected from {websocket.client}")
    
    message_buffer = get_message_buffer()
    
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


@router.get("/messages/recent")
async def get_recent_messages(limit: int = 50):
    """Get recent Kafka messages"""
    message_buffer = get_message_buffer()
    messages = list(message_buffer)[-limit:]
    return {"count": len(messages), "messages": messages}
