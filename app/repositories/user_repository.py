from app.repositories.base_repository import BaseRepository
from app.models.user import UserInDB
from motor.motor_asyncio import AsyncIOMotorCollection
from typing import Optional

class UserRepository(BaseRepository[UserInDB]):
    def __init__(self, collection: AsyncIOMotorCollection):
        super().__init__(collection, UserInDB)

    async def get_by_email(self, email: str) -> Optional[UserInDB]:
        return await self.get_by_field("email", email)
    
    async def get_by_phone_number(self, phone_number: str) -> Optional[UserInDB]:
        return await self.get_by_field("phone_number", phone_number)
    
    async def get_by_identifier(self, identifier: str) -> Optional[UserInDB]:
        """
        Recherche un utilisateur par email ou numéro de téléphone
        """
        doc = await self.collection.find_one({
            "$or": [
                {"email": identifier},
                {"phone_number": identifier}
            ]
        })
        if doc:
            return UserInDB(**doc)  # ✅ Utilisez UserInDB directement au lieu de self.model
        return None