from datetime import datetime, timezone
from app.core.database import get_database
from app.core.config import settings
from typing import List, Optional
import json
import redis.asyncio as redis

class AdService:
    def __init__(self, db):
        self.db = db
        self.collection = self.db.advertisements
        self.redis = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        self.cache_ttl = settings.REDIS_CACHE_TTL_SECONDS

    async def get_active_ads(self, limit: int = 10, skip: int = 0, target_group: Optional[str] = None) -> List[dict]:
        cache_key = f"ads:active:{target_group if target_group else 'all'}:{limit}:{skip}"
        
        # Try to get from cache
        try:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception:
            # Fallback to DB if redis fails
            pass

        now = datetime.now(timezone.utc)
        query = {
            "start_date": {"$lte": now},
            "end_date": {"$gte": now},
            "is_active": True
        }
        if target_group:
            query["target_group"] = target_group

        cursor = self.collection.find(query).skip(skip).limit(limit)
        ads = await cursor.to_list(length=limit)
        
        # Convert ObjectId and datetime to string for JSON serialization
        serialized_ads = []
        for ad in ads:
            ad_dict = dict(ad)
            if '_id' in ad_dict:
                ad_dict['_id'] = str(ad_dict['_id'])
            if 'start_date' in ad_dict:
                ad_dict['start_date'] = ad_dict['start_date'].isoformat()
            if 'end_date' in ad_dict:
                ad_dict['end_date'] = ad_dict['end_date'].isoformat()
            serialized_ads.append(ad_dict)

        # Save to cache
        try:
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(serialized_ads))
        except Exception:
            pass
        
        return ads

    async def count_active_ads(self, target_group: Optional[str] = None) -> int:
        now = datetime.now(timezone.utc)
        query = {
            "start_date": {"$lte": now},
            "end_date": {"$gte": now},
            "is_active": True
        }
        if target_group:
            query["target_group"] = target_group
        return await self.collection.count_documents(query)

    async def close(self):
        await self.redis.close()

async def get_ad_service():
    db = await get_database()
    return AdService(db)
