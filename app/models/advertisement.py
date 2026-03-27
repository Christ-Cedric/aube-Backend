from pydantic import BaseModel, HttpUrl, field_validator
from typing import Optional
from datetime import datetime

class AdvertisementDB(BaseModel):
    title: str
    message: str
    image_url: Optional[HttpUrl] = None
    start_date: datetime
    end_date: datetime
    target_group: Optional[str] = None
    is_active: bool = True
    created_at: datetime

    @field_validator('end_date')
    def validate_dates(cls, v, values):
        if 'start_date' in values.data and v <= values.data['start_date']:
            raise ValueError('end_date must be after start_date')
        return v

class AdvertisementResponse(AdvertisementDB):
    pass
