from fastapi import APIRouter, Depends, Query
from app.services.ad_service import AdService, get_ad_service
from app.models.advertisement import AdvertisementResponse
from typing import List, Optional

router = APIRouter()

@router.get("/ads", response_model=dict)
async def get_ads(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    target_group: Optional[str] = None,
    service: AdService = Depends(get_ad_service)
):
    skip = (page - 1) * limit
    ads = await service.get_active_ads(limit, skip, target_group)
    total = await service.count_active_ads(target_group)
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "ads": ads
    }
