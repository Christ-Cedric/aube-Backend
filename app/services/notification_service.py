import redis.asyncio as redis
from app.core.config import settings
import json
import logging

class NotificationService:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        self.pubsub = self.redis.pubsub()

    async def publish(self, channel: str, message: dict):
        await self.redis.publish(channel, json.dumps(message))

    async def subscribe(self, channel: str):
        await self.pubsub.subscribe(channel)

    async def get_message(self):
        message = await self.pubsub.get_message(ignore_subscribe_messages=True)
        if message:
            try:
                return json.loads(message["data"])
            except json.JSONDecodeError:
                return message["data"]
        return None
        
    async def close(self):
        await self.redis.close()

notification_service = NotificationService()
