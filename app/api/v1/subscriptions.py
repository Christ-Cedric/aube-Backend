from fastapi import APIRouter, Depends, HTTPException, status
from app.models.subscription import SubscriptionRequest, SubscriptionResponse, CheckSubscriptionRequest
from app.services.subscription_service import SubscriptionService, get_subscription_service
from app.utils.exceptions import ConflictError, NotFoundError

router = APIRouter()

@router.post("/request_subscription", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def request_subscription(
    request: SubscriptionRequest,
    service: SubscriptionService = Depends(get_subscription_service)
):
    try:
        return await service.create_subscription_request(request)
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.detail)

@router.post("/check_subscription", response_model=SubscriptionResponse)
async def check_subscription(
    request: CheckSubscriptionRequest,
    service: SubscriptionService = Depends(get_subscription_service)
):
    try:
        return await service.check_subscription(request.device_id, request.activation_key)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
