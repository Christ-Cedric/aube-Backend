from app.core.database import db
from app.models.user import User, UserInDB
from app.models.auth import UserSignup, UserLogin, Token
from app.models.device import DeviceCreate, DeviceDB
from app.core.security import get_password_hash, verify_password, create_access_token
from fastapi import HTTPException, status
from datetime import datetime, timezone
import uuid

import redis.asyncio as redis
from app.core.config import settings
import json

class UserService:
    def __init__(self, db):
        self.collection = db["users"]
        self.db_devices = db["user_devices"]
        self.redis = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)

    async def create_user(self, user_in: UserSignup) -> User:
        existing_user = await self.collection.find_one({"email": user_in.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )
        
        hashed_password = get_password_hash(user_in.password)
        db_user = UserInDB(
            id=uuid.uuid4(),
            email=user_in.email,
            full_name=user_in.full_name,
            hashed_password=hashed_password,
            created_at=datetime.now(timezone.utc),
            is_active=True
        )
        
        await self.collection.insert_one(db_user.model_dump(mode='json'))
        return User(**db_user.model_dump())

    async def authenticate(self, user_in: UserLogin) -> Token:
        user = await self.collection.find_one({"email": user_in.email})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not verify_password(user_in.password, user["hashed_password"]):
             raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        access_token = create_access_token(subject=user["id"])
        return Token(
            access_token=access_token,
            token_type="bearer"
        )

    async def update_profile(self, user_id: uuid.UUID, data: dict) -> User:
        # Invalidated cache
        try:
            await self.redis.delete(f"user:profile:{str(user_id)}")
        except Exception:
            pass
        
        # Filter out None values
        update_data = {k: v for k, v in data.items() if v is not None}
        if not update_data:
            return None
            
        await self.collection.update_one(
            {"id": str(user_id)},
            {"$set": update_data}
        )
        
        updated_user = await self.collection.find_one({"id": str(user_id)})
        return User(**updated_user)

    async def add_device(self, user_id: uuid.UUID, device_in: DeviceCreate) -> DeviceDB:
        # Check if device exists for user
        existing = await self.db_devices.find_one({"user_id": str(user_id), "device_id": str(device_in.device_id)})
        if existing:
            # Update last used
            await self.db_devices.update_one(
                {"_id": existing["_id"]},
                {"$set": {"last_used": datetime.now(timezone.utc), "fcm_token": device_in.fcm_token}}
            )
            # Invalidate device cache
            try:
                await self.redis.delete(f"user:devices:{str(user_id)}")
            except Exception:
                pass
            return DeviceDB(**(await self.db_devices.find_one({"_id": existing["_id"]})))

        device_db = DeviceDB(
            **device_in.dict(),
            user_id=user_id,
            last_used=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc)
        )
        
        device_dict = device_db.dict()
        # Convert UUIDs to strings for MongoDB
        device_dict['user_id'] = str(device_dict['user_id'])
        device_dict['device_id'] = str(device_dict['device_id'])
        await self.db_devices.insert_one(device_dict)
        # Invalidate device cache
        try:
            await self.redis.delete(f"user:devices:{str(user_id)}")
        except Exception:
            pass
        return device_db

    async def list_devices(self, user_id: uuid.UUID):
        # Try cache
        cache_key = f"user:devices:{str(user_id)}"
        try:
            cached = await self.redis.get(cache_key)
            if cached:
                devices_data = json.loads(cached)
                return [DeviceDB(**d) for d in devices_data]
        except Exception:
            pass

        cursor = self.db_devices.find({"user_id": str(user_id)})
        devices = await cursor.to_list(length=100)
        
        result = [DeviceDB(**d) for d in devices]
        
        # Cache result
        # Serialize list of models
        serialized = [d.model_dump(mode='json') for d in result]
        try:
            await self.redis.setex(cache_key, 300, json.dumps(serialized))
        except Exception:
            pass
        
        return result

    async def remove_device(self, user_id: uuid.UUID, device_id: uuid.UUID):
        result = await self.db_devices.delete_one({"user_id": str(user_id), "device_id": str(device_id)})
        # Invalidate device cache
        try:
            await self.redis.delete(f"user:devices:{str(user_id)}")
        except Exception:
            pass
        return result.deleted_count > 0

async def get_user_service():
    from app.core.database import get_database
    db = await get_database()
    return UserService(db)
