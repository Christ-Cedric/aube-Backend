from app.core.database import db
from app.models.user import User, UserInDB
from app.models.session import UserSession
from app.models.device import DeviceDB
from app.schemas.user import UserCreate, UserOut, Token, UserLogin, UserUpdate, UserChangePassword
from app.schemas.subscription import DeviceCreate, DeviceOut
from app.core.security import get_password_hash, verify_password, create_access_token
from app.repositories.user_repository import UserRepository
from app.repositories.device_repository import DeviceRepository
from fastapi import HTTPException, status
from datetime import datetime, timedelta, timezone
import uuid
from app.core.config import settings
from app.core.cache import cache
import json

class UserService:
    def __init__(self, db):
        self.user_repo = UserRepository(db["users"])
        self.device_repo = DeviceRepository(db["user_devices"])
        self.session_repo = db["user_sessions"]

    async def create_user(self, user_in: UserCreate) -> UserOut:
        # Vérifier si le numéro de téléphone existe déjà
        existing_user = await self.user_repo.get_by_phone_number(user_in.phone_number)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this phone number already exists"
            )
        
        # Vérifier si l'email existe déjà (si fourni)
        if user_in.email:
            existing_email = await self.user_repo.get_by_email(user_in.email)
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User with this email already exists"
                )
        
        hashed_password = get_password_hash(user_in.password)
        db_user = UserInDB(
            id=uuid.uuid4(),
            phone_number=user_in.phone_number,
            email=user_in.email,
            full_name=user_in.full_name,
            hashed_password=hashed_password,
            created_at=datetime.now(timezone.utc),
            is_active=True
        )
        
        await self.user_repo.create(db_user)
        return UserOut(**db_user.model_dump())

    async def authenticate(self, user_in: UserLogin, ip_address: str = None, user_agent: str = None) -> Token:
        # Rechercher l'utilisateur par email ou numéro de téléphone
        user = await self.user_repo.get_by_identifier(user_in.identifier)
        
        if not user or not verify_password(user_in.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled",
            )

        # Update last login info
        await self.user_repo.update(user.id, {
            "last_login": datetime.now(timezone.utc),
            "login_count": user.login_count + 1
        })

        access_token = create_access_token(subject=user.id)
        refresh_token = str(uuid.uuid4())
        
        session = UserSession(
            user_id=user.id,
            device_id=uuid.UUID(int=0),
            refresh_token_hash=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30)
        )
        await self.session_repo.insert_one(session.model_dump(mode='json'))

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=15 * 60,
            user=UserOut(**user.model_dump())
        )

    async def refresh_token(self, refresh_token: str) -> Token:
        session_doc = await self.session_repo.find_one({
            "refresh_token_hash": refresh_token,
            "is_active": True,
            "expires_at": {"$gt": datetime.now(timezone.utc)}
        })
        
        if not session_doc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
            
        session = UserSession(**session_doc)
        access_token = create_access_token(subject=session.user_id)
        
        new_refresh_token = str(uuid.uuid4())
        await self.session_repo.update_one(
            {"session_id": str(session.session_id)},
            {"$set": {
                "refresh_token_hash": new_refresh_token,
                "created_at": datetime.now(timezone.utc)
            }}
        )
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=15 * 60,
            user=UserOut(**session.model_dump()) # Attention: session n'est pas user. Il faut récupérer le user.
        )

    async def logout(self, refresh_token: str):
        await self.session_repo.update_one(
            {"refresh_token_hash": refresh_token},
            {"$set": {"is_active": False}}
        )

    async def change_password(self, user_id: uuid.UUID, password_data: UserChangePassword):
        user = await self.user_repo.get(user_id)
        if not user or not verify_password(password_data.old_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect old password"
            )
            
        hashed_password = get_password_hash(password_data.new_password)
        await self.user_repo.update(user_id, {"hashed_password": hashed_password})
        
        await self.session_repo.update_many(
            {"user_id": str(user_id)},
            {"$set": {"is_active": False}}
        )

    async def update_profile(self, user_id: uuid.UUID, data: dict) -> UserOut:
        await cache.delete(f"user:profile:{str(user_id)}")
        updated_user = await self.user_repo.update(user_id, data)
        return UserOut(**updated_user.model_dump())

    async def register_current_device(self, user_id: uuid.UUID, device_in: DeviceCreate) -> DeviceOut:
        """
        Enregistre/met à jour l'appareil actuel de l'utilisateur.
        """
        device_id_str = str(device_in.device_id)
        user_id_str = str(user_id)
        
        existing = await self.device_repo.get_by_user_and_device(user_id, device_in.device_id)
        if existing:
            # Mettre à jour
            update_data = {
                "device_name": device_in.device_name,
                "os_type": device_in.os_type,
                "is_primary": device_in.is_primary,
                "fcm_token": device_in.fcm_token,
                "last_used": datetime.now(timezone.utc),
                "is_active": True
            }
            await self.device_repo.update(device_in.device_id, update_data)
            updated = await self.device_repo.get_by_user_and_device(user_id, device_in.device_id)
            await cache.delete(f"user:devices:{user_id_str}")
            return DeviceOut(
                device_id=device_in.device_id,
                user_id=user_id,
                device_name=updated.device_name,
                os_type=updated.os_type,
                is_primary=updated.is_primary,
                is_active=updated.is_active,
                created_at=updated.created_at,
                last_used=updated.last_used,
                fcm_token=updated.fcm_token
            )

        # Créer nouveau device
        device_db = DeviceDB(
            device_id=device_id_str,
            user_id=user_id_str,
            device_name=device_in.device_name,
            os_type=device_in.os_type,
            is_primary=device_in.is_primary,
            fcm_token=device_in.fcm_token,
            is_active=True,
            last_used=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc)
        )
        
        await self.device_repo.create(device_db)
        await cache.delete(f"user:devices:{user_id_str}")
        
        return DeviceOut(
            device_id=device_in.device_id,
            user_id=user_id,
            device_name=device_db.device_name,
            os_type=device_db.os_type,
            is_primary=device_db.is_primary,
            is_active=device_db.is_active,
            created_at=device_db.created_at,
            last_used=device_db.last_used,
            fcm_token=device_db.fcm_token
        )

    async def list_devices(self, user_id: uuid.UUID):
        cache_key = f"user:devices:{str(user_id)}"
        cached = await cache.get(cache_key)
        if cached:
            devices_data = json.loads(cached)
            return [DeviceOut(**d) for d in devices_data]

        devices = await self.device_repo.list_by_user(user_id)
        result = []
        for d in devices:
            result.append(DeviceOut(
                device_id=uuid.UUID(d.device_id),
                user_id=uuid.UUID(d.user_id),
                device_name=d.device_name,
                os_type=d.os_type,
                is_primary=d.is_primary,
                is_active=d.is_active,
                created_at=d.created_at,
                last_used=d.last_used,
                fcm_token=d.fcm_token
            ))
        
        # Sérialiser pour le cache
        cache_data = [d.model_dump(mode='json') for d in result]
        await cache.setex(cache_key, 300, json.dumps(cache_data))
        
        return result

    async def remove_device(self, user_id: uuid.UUID, device_id: uuid.UUID):
        success = await self.device_repo.delete(device_id)
        if success:
            await cache.delete(f"user:devices:{str(user_id)}")
        return success

async def get_user_service():
    from app.core.database import get_database
    db = await get_database()
    return UserService(db)