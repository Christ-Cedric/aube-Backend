from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, timezone
from uuid import UUID

class DeviceBase(BaseModel):
    device_name: str
    os_type: str = "Unknown"  # iOS, Android, Web
    fcm_token: Optional[str] = None
    is_primary: bool = False

class DeviceCreate(DeviceBase):
    device_id: UUID  # Changé de str à UUID pour l'API

class DeviceDB(DeviceBase):
    device_id: str  # Reste str pour MongoDB
    user_id: str    # Reste str pour MongoDB
    is_active: bool = True
    last_used: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator('device_id', 'user_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        """Convertit UUID en string si nécessaire"""
        if isinstance(v, UUID):
            return str(v)
        return v