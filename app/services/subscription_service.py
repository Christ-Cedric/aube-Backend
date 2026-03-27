from datetime import datetime, timezone
import uuid
import secrets
from app.core.database import get_database
from app.core.config import settings
from app.models.subscription import SubscriptionRequest, SubscriptionDB
from app.utils.exceptions import ConflictError, NotFoundError
from app.core.cache import cache
import json

class SubscriptionService:
    def __init__(self, db):
        self.db = db
        self.collection = self.db.subscriptions
        self.cache_ttl = 300  # 5 minutes for subscription status


    async def create_subscription_request(self, user_id: uuid.UUID, request: SubscriptionRequest) -> SubscriptionDB:
        # Check if device exists, if not, create it
        device = await self.db.user_devices.find_one({"device_id": str(request.device_id)})
        if not device:
            new_device = {
                "device_id": str(request.device_id),
                "user_id": user_id,
                "device_name": request.device_name,
                "os_type": request.os_type,
                "is_primary": False,
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
                "last_used": datetime.now(timezone.utc)
            }
            await self.db.user_devices.insert_one(new_device)
        else:
            # Update last used and info
            await self.db.user_devices.update_one(
                {"device_id": str(request.device_id)},
                {"$set": {
                    "last_used": datetime.now(timezone.utc),
                    "device_name": request.device_name,
                    "os_type": request.os_type
                }}
            )

        # Check for existing active subscription
        existing = await self.collection.find_one({
            "device_id": str(request.device_id),
            "status": {"$in": ["pending", "validated"]}
        })
        if existing:
            raise ConflictError("Active subscription already exists for this device")

        activation_key = f"ACT-{datetime.now(timezone.utc).year}-{secrets.token_hex(4).upper()}"
        
        subscription_data = {
            "id": str(uuid.uuid4()),
            "plan_name": request.plan_name,
            "amount": request.amount,
            "duration_days": request.duration_days,
            "device_id": str(request.device_id),
            "user_id": str(user_id),
            "phone_number": request.phone_number,
            "months": request.months,
            "activation_key": activation_key,
            "status": "pending",
            "created_at": datetime.now(timezone.utc),
            "expires_at": None,
            "validated_by": None,
            "validated_at": None
        }
        
        await self.collection.insert_one(subscription_data)
        return SubscriptionDB(**subscription_data)

    async def check_subscription(self, device_id: uuid.UUID = None, activation_key: str = None) -> dict:
        # Construct cache key
        cache_key = None
        if device_id:
            cache_key = f"subscription:device:{device_id}"
        elif activation_key:
            cache_key = f"subscription:key:{activation_key}"

        if cache_key:
            cached_data = await cache.get(cache_key)
            if cached_data:
                return json.loads(cached_data)


        query = {}
        if device_id:
            query["device_id"] = str(device_id)
        elif activation_key:
            query["activation_key"] = activation_key
        
        sub = await self.collection.find_one(query)
        if not sub:
            raise NotFoundError("Subscription not found")
            
        # Check expiration
        now = datetime.now(timezone.utc)
        if sub["status"] == "validated" and sub.get("expires_at") and sub["expires_at"].replace(tzinfo=timezone.utc) < now:
            await self.collection.update_one(
                {"_id": sub["_id"]},
                {"$set": {"status": "expired"}}
            )
            sub["status"] = "expired"
            # Invalidate cache
            if cache_key:
                await cache.delete(cache_key)


        remaining_days = 0
        if sub["status"] == "validated" and sub.get("expires_at"):
             delta = sub["expires_at"].replace(tzinfo=timezone.utc) - now
             remaining_days = max(0, delta.days)

        result = {**sub, "remaining_days": remaining_days}
        
        # Serialize for cache
        result_to_cache = result.copy()
        if '_id' in result_to_cache:
            result_to_cache['_id'] = str(result_to_cache['_id'])
        if 'created_at' in result_to_cache and isinstance(result_to_cache['created_at'], datetime):
            result_to_cache['created_at'] = result_to_cache['created_at'].isoformat()
        if 'expires_at' in result_to_cache and result_to_cache['expires_at'] and isinstance(result_to_cache['expires_at'], datetime):
            result_to_cache['expires_at'] = result_to_cache['expires_at'].isoformat()
        if 'validated_at' in result_to_cache and result_to_cache['validated_at'] and isinstance(result_to_cache['validated_at'], datetime):
            result_to_cache['validated_at'] = result_to_cache['validated_at'].isoformat()

        if cache_key:
            await cache.setex(cache_key, self.cache_ttl, json.dumps(result_to_cache))


        return result

    async def close(self):
        pass  # No cleanup needed for in-memory cache


async def get_subscription_service():
    db = await get_database()
    return SubscriptionService(db)
