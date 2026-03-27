from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4

class DeviceBase(BaseModel):
    device_name: str
    os_type: str  # iOS, Android, Web
    fcm_token: Optional[str] = None
    is_primary: bool = False

class DeviceCreate(DeviceBase):
    device_id: UUID

class DeviceDB(DeviceBase):
    device_id: UUID
    user_id: UUID
    last_used: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
