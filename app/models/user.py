from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4
import re

class User(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    email: Optional[EmailStr] = None  # Email devient optionnel
    phone_number: str  # Numéro obligatoire
    full_name: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    login_count: int = 0

    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v):
        # Format international simple (peut être adapté selon vos besoins)
        pattern = r'^\+?[1-9]\d{1,14}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid phone number format')
        return v

class UserInDB(User):
    hashed_password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None