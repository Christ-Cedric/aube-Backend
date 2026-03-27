from datetime import datetime, timedelta, timezone
from typing import Optional, Any
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"

def create_access_token(subject: str | Any, expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Default 15 minutes
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password[:72])

from app.core.cache import cache
import json
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.models.user import User
from app.schemas.user import TokenPayload
from app.core.database import get_database
from uuid import UUID

from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        if token_data.sub is None:
            raise credentials_exception
    except (JWTError, Exception):
        raise credentials_exception
        
    user_id = token_data.sub
    
    # Try cache
    cached = await cache.get(f"user:profile:{user_id}")
    if cached:
        return User(**json.loads(cached))

    db = await get_database()
    user_repo = UserRepository(db["users"])
    user_data = await user_repo.get(user_id)
    if user_data is None:
        raise credentials_exception
    
    user = User(**user_data.model_dump())
    
    # Store in cache
    await cache.setex(f"user:profile:{user_id}", 600, user.model_dump_json())
        
    return user

