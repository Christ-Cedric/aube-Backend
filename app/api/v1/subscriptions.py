from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.schemas.subscription import SubscriptionRequest, SubscriptionResponse
from app.services.subscription_service import SubscriptionService, get_subscription_service
from app.utils.exceptions import ConflictError, NotFoundError
from app.core.security import get_current_user
from app.models.user import User
from uuid import UUID

router = APIRouter(
    prefix="/subscriptions",
    tags=["Subscriptions"]
)

@router.post("/request", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def request_subscription(
    request: SubscriptionRequest,
    current_user: User = Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service)
):
    try:
        result = await service.create_subscription_request(current_user.id, request)
        return SubscriptionResponse(
            id=result.id,
            plan_name=result.plan_name,
            amount=result.amount,
            duration_days=result.duration_days,
            device_id=result.device_id,
            user_id=result.user_id,
            phone_number=result.phone_number,
            months=result.months,
            activation_key=result.activation_key,
            status=result.status,
            created_at=result.created_at,
            expires_at=result.expires_at,
            validated_by=result.validated_by,
            validated_at=result.validated_at,
            remaining_days=0
        )
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/my-subscription", response_model=SubscriptionResponse)
async def get_my_subscription(
    device_id: UUID = Query(..., description="Device ID"),
    current_user: User = Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service)
):
    try:
        result = await service.check_subscription(device_id=device_id)
        return SubscriptionResponse(**result)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="No subscription found for this device"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))