from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4
import re

class SubscriptionRequest(BaseModel):
    device_id: UUID
    phone_number: str
    months: int = Field(..., ge=1, le=12)
    plan_name: str = "Standard"
    amount: float = Field(..., gt=0)
    duration_days: int = Field(..., gt=0)
    device_name: Optional[str] = "Unknown"
    os_type: Optional[str] = "Unknown"

    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v):
        pattern = r'^\+[1-9]\d{1,14}$'
        if not re.match(pattern, v):
            raise ValueError('Phone number must be in E.164 format (e.g., +1234567890)')
        return v

# Alias pour compatibilité
SubscriptionCreate = SubscriptionRequest

class CheckSubscriptionRequest(BaseModel):
    device_id: Optional[UUID] = None
    activation_key: Optional[str] = None

    @field_validator('activation_key')
    @classmethod
    def check_one_required(cls, v, info):
        if not v and not info.data.get('device_id'):
            raise ValueError('Either device_id or activation_key must be provided')
        return v

class SubscriptionDB(BaseModel):
    id: str
    plan_name: str
    amount: float
    duration_days: int
    device_id: str
    user_id: str
    phone_number: str
    months: int
    activation_key: str
    status: str  # pending, validated, expired, suspended
    created_at: datetime
    expires_at: Optional[datetime] = None
    validated_by: Optional[str] = None
    validated_at: Optional[datetime] = None

class SubscriptionResponse(BaseModel):
    id: str
    plan_name: str
    amount: float
    duration_days: int
    device_id: str
    user_id: str
    phone_number: str
    months: int
    activation_key: str
    status: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    validated_by: Optional[str] = None
    validated_at: Optional[datetime] = None
    remaining_days: int = 0

# Alias pour compatibilité
SubscriptionOut = SubscriptionResponse

# Schemas pour les devices (utilisés par user_service)
class DeviceCreate(BaseModel):
    device_id: UUID
    device_name: str = "Unknown Device"
    os_type: str = "Unknown"
    fcm_token: Optional[str] = None
    is_primary: bool = False

class DeviceOut(BaseModel):
    device_id: UUID
    user_id: UUID
    device_name: str
    os_type: str
    is_primary: bool
    is_active: bool
    created_at: datetime
    last_used: datetime

class Config:
        from_attributes = True    