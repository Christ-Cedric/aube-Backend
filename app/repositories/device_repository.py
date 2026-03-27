from app.repositories.base_repository import BaseRepository
from app.models.device import DeviceDB
from motor.motor_asyncio import AsyncIOMotorCollection
from uuid import UUID
from typing import List

class DeviceRepository(BaseRepository[DeviceDB]):
    def __init__(self, collection: AsyncIOMotorCollection):
        super().__init__(collection, DeviceDB)

    async def list_by_user(self, user_id: UUID) -> List[DeviceDB]:
        return await self.list(filter_query={"user_id": str(user_id)})

    async def get_by_user_and_device(self, user_id: UUID, device_id: UUID) -> DeviceDB | None:
        doc = await self.collection.find_one({
            "user_id": str(user_id),
            "device_id": str(device_id)
        })
        return DeviceDB(**doc) if doc else None
