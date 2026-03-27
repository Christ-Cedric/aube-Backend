from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID
import re

class SubscriptionRequest(BaseModel):
    device_id: UUID
    phone_number: str
    months: int = Field(..., ge=1, le=12)

    @field_validator('phone_number')
    def validate_phone_number(cls, v):
        pattern = r'^\+[1-9]\d{1,14}$'
        if not re.match(pattern, v):
            raise ValueError('Phone number must be in E.164 format (e.g., +1234567890)')
        return v

class CheckSubscriptionRequest(BaseModel):
    device_id: Optional[UUID] = None
    activation_key: Optional[str] = None

    @field_validator('activation_key')
    def check_one_required(cls, v, values):
        if not v and not values.data.get('device_id'):
            raise ValueError('Either device_id or activation_key must be provided')
        return v

class SubscriptionDB(BaseModel):
    device_id: UUID
    phone_number: str
    months: int
    activation_key: str
    status: str  # pending, validated, expired, suspended
    created_at: datetime
    expires_at: Optional[datetime] = None
    validated_by: Optional[UUID] = None
    validated_at: Optional[datetime] = None

class SubscriptionResponse(SubscriptionDB):
    remaining_days: int = 0
