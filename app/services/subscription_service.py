from datetime import datetime, timezone
import uuid
import secrets
from app.core.database import get_database
from app.core.config import settings
from app.models.subscription import SubscriptionRequest, SubscriptionDB
from app.utils.exceptions import ConflictError, NotFoundError
import json
import redis.asyncio as redis

class SubscriptionService:
    def __init__(self, db):
        self.db = db
        self.collection = self.db.subscriptions
        self.redis = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        self.cache_ttl = 300  # 5 minutes for subscription status

    async def create_subscription_request(self, request: SubscriptionRequest) -> SubscriptionDB:
        # Check for existing active subscription
        existing = await self.collection.find_one({
            "device_id": str(request.device_id),
            "status": {"$in": ["pending", "validated"]}
        })
        if existing:
            raise ConflictError("Active subscription already exists for this device")

        activation_key = f"ACT-{datetime.now(timezone.utc).year}-{secrets.token_hex(4).upper()}"
        
        subscription_data = {
            "device_id": str(request.device_id),
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
            try:
                cached_data = await self.redis.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            except Exception:
                pass

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
                 try:
                    await self.redis.delete(cache_key)
                 except Exception:
                    pass

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
            try:
                await self.redis.setex(cache_key, self.cache_ttl, json.dumps(result_to_cache))
            except Exception:
                pass

        return result

    async def close(self):
        await self.redis.close()

async def get_subscription_service():
    db = await get_database()
    return SubscriptionService(db)
