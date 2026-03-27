from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID
import re

# User Schemas
class UserBase(BaseModel):
    phone_number: str  # Obligatoire
    email: Optional[EmailStr] = None  # Optionnel
    full_name: Optional[str] = None

    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v):
        pattern = r'^\+?[1-9]\d{1,14}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid phone number format. Use international format (e.g., +33612345678)')
        return v

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    # L'utilisateur peut se connecter avec email OU numéro de téléphone
    identifier: str  # Email ou numéro de téléphone
    password: str

    @field_validator('identifier')
    @classmethod
    def validate_identifier(cls, v):
        if not v:
            raise ValueError('Email or phone number is required')
        return v

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None

class UserOut(BaseModel):
    id: UUID
    phone_number: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Auth Schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: Optional['UserOut'] = None

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None

class UserChangePassword(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)