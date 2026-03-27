from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4

class UserSession(BaseModel):
    session_id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    device_id: UUID
    refresh_token_hash: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
