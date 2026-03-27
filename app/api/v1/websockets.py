from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, status
from app.services.notification_service import NotificationService
from app.core.security import settings
from jose import jwt, JWTError
import logging
import asyncio
import redis.asyncio as redis
import json

router = APIRouter()
logger = logging.getLogger(__name__)

async def get_user_id_from_token(token: str):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError:
        return None

@router.websocket("/ws/notifications/{device_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    device_id: str,
    token: str = Query(...)
):
    user_id = await get_user_id_from_token(token)
    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    service = NotificationService()
    await service.subscribe("subscription_events")
    await service.subscribe("ad_events")
    
    # Subscribe to user specific events for force logout
    user_channel = f"user_events:{user_id}"
    await service.subscribe(user_channel)

    # Redis for online status
    r = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    online_key = f"user:online:{user_id}"

    try:
        # Mark as online
        await r.setex(online_key, 60, "online")

        while True:
            try:
                # Refresh online status
                await r.setex(online_key, 60, "online")
                
                # Check for Redis messages
                message = await service.get_message()
                if message:
                    if isinstance(message, dict):
                        # Handle force logout
                        if message.get("event") == "force_disconnect":
                            await websocket.send_json({"event": "force_disconnect", "message": "Session terminated by admin"})
                            await websocket.close()
                            break

                        if message.get("device_id") == device_id or message.get("event") == "new_advertisement":
                            await websocket.send_json(message)
            except redis.ConnectionError:
                 # Log error but try to keep connection alive for a bit? 
                 # Or just ignore one failure.
                 logger.warning(f"Redis connection error for client {device_id}")
            except Exception as e:
                 logger.error(f"Error in websocket loop: {e}")
            
            # Keep alive and handle client disconnects
            # Small sleep to prevent busy loop if no messages
            await asyncio.sleep(0.1) 
    except WebSocketDisconnect:
        logger.info(f"Client {device_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await r.delete(online_key)
        await r.close()
        await service.close()
