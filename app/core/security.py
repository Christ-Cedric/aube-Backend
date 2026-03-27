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
    return pwd_context.hash(password)

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.models.user import User
from app.core.database import get_database
from uuid import UUID

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    # Try cache first
    import redis.asyncio as redis
    import json
    r = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    try:
        cached = await r.get(f"user:profile:{user_id}")
        if cached:
            return User(**json.loads(cached))
    except Exception as e:
        # Fallback to DB if redis fails
        pass

    db = await get_database()
    user = await db.users.find_one({"id": user_id})
    if user is None:
        await r.close()
        raise credentials_exception
    
    # helper to process datetime for json
    user_data = dict(user)
    if '_id' in user_data:
        del user_data['_id'] # remove mongo id
    
    # Store in cache
    try:
        # Use pydantic model dump which handles serialization better usually, but here we have dict from mongo
        # User model handles conversions. Let's dump the User object.
        user_obj = User(**user)
        await r.setex(f"user:profile:{user_id}", 600, user_obj.model_dump_json())
    except Exception:
        pass
    finally:
        await r.close()
        
    return User(**user)
