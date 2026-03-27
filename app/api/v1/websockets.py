from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from app.core.config import settings
from jose import jwt, JWTError
import logging
import asyncio
from datetime import datetime, timezone

router = APIRouter()
logger = logging.getLogger(__name__)

async def get_user_id_from_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload.get("sub")
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
        logger.warning(f"WebSocket connection rejected for device {device_id}: invalid token")
        return

    await websocket.accept()
    logger.info(f"WebSocket accepted for user {user_id}, device {device_id}")

    from app.core.database import db
    database = db.db
    
    # Track last check time for polling
    last_check = datetime.now(timezone.utc)
    
    try:
        # Check if device is active before proceeding
        device_doc = await database.user_devices.find_one({"device_id": device_id})
        if device_doc and not device_doc.get("is_active", True):
            await websocket.send_json({
                "event": "device_deactivated", 
                "message": "This device has been deactivated by admin"
            })
            await websocket.close()
            return

        while True:
            # Poll database every 5 seconds for changes
            await asyncio.sleep(5)
            
            now = datetime.now(timezone.utc)
            
            # 1. Check for subscription updates
            subscription = await database.subscriptions.find_one({
                "device_id": device_id,
                "updated_at": {"$gt": last_check}
            })
            
            if subscription:
                await websocket.send_json({
                    "event": "subscription_updated",
                    "status": subscription.get("status"),
                    "expires_at": subscription.get("expires_at").isoformat() if subscription.get("expires_at") else None,
                    "remaining_days": (subscription.get("expires_at").replace(tzinfo=timezone.utc) - now).days if subscription.get("expires_at") else 0
                })
                logger.info(f"Sent subscription update to device {device_id}")
            
            # 2. Check if device has been deactivated
            device = await database.user_devices.find_one({
                "device_id": device_id,
                "updated_at": {"$gt": last_check}
            })
            
            if device and not device.get("is_active", True):
                await websocket.send_json({
                    "event": "device_deactivated",
                    "message": "Device has been deactivated by admin"
                })
                await websocket.close()
                break
            
            # 3. Check for new advertisements
            ads_cursor = database.advertisements.find({
                "is_active": True,
                "created_at": {"$gt": last_check}
            }).limit(10)
            
            ads = await ads_cursor.to_list(length=10)
            for ad in ads:
                await websocket.send_json({
                    "event": "new_advertisement",
                    "ad": {
                        "id": str(ad["_id"]),
                        "title": ad.get("title", ""),
                        "image_url": ad.get("image_url", ""),
                        "link_url": ad.get("link_url", "")
                    }
                })
                logger.info(f"Sent new ad to device {device_id}")
            
            last_check = now
            
            # Check for client messages (heartbeat)
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
            except asyncio.TimeoutError:
                pass  # No message from client, continue
                
    except WebSocketDisconnect:
        logger.info(f"Client {device_id} (User {user_id}) disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        import traceback
        traceback.print_exc()
