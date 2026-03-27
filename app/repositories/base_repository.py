from typing import TypeVar, Generic, Optional, List
from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel
from uuid import UUID

T = TypeVar('T', bound=BaseModel)

class BaseRepository(Generic[T]):
    def __init__(self, collection: AsyncIOMotorCollection, model: type[T]):
        self.collection = collection
        self.model = model  # ✅ Assurez-vous que cette ligne existe

    async def create(self, entity: T) -> T:
        doc = entity.model_dump(mode='json')
        await self.collection.insert_one(doc)
        return entity

    async def get(self, entity_id: UUID) -> Optional[T]:
        doc = await self.collection.find_one({"id": str(entity_id)})
        if doc:
            return self.model(**doc)
        return None

    async def get_by_field(self, field: str, value: any) -> Optional[T]:
        doc = await self.collection.find_one({field: value})
        if doc:
            return self.model(**doc)
        return None

    async def update(self, entity_id: UUID, data: dict) -> Optional[T]:
        await self.collection.update_one(
            {"id": str(entity_id)},
            {"$set": data}
        )
        return await self.get(entity_id)

    async def delete(self, entity_id: UUID) -> bool:
        result = await self.collection.delete_one({"id": str(entity_id)})
        return result.deleted_count > 0

    async def list_all(self) -> List[T]:
        docs = await self.collection.find().to_list(None)
        return [self.model(**doc) for doc in docs]