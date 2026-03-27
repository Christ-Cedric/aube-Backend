from fastapi import APIRouter, Depends, HTTPException, status
from app.models.user import User, UserUpdate
from app.models.device import DeviceCreate, DeviceDB
from app.services.user_service import UserService, get_user_service
from app.core.security import get_current_user # Need to implement this dependency
from typing import List
from uuid import UUID

router = APIRouter(prefix="/user", tags=["User Profile"])

@router.get("/profile", response_model=User)
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user

@router.patch("/profile", response_model=User)
async def update_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    return await service.update_profile(current_user.id, update_data.dict(exclude_unset=True))

@router.get("/devices", response_model=List[DeviceDB])
async def list_devices(
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    return await service.list_devices(current_user.id)

@router.post("/devices", response_model=DeviceDB)
async def add_device(
    device_in: DeviceCreate,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    return await service.add_device(current_user.id, device_in)

@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_device(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    success = await service.remove_device(current_user.id, device_id)
    if not success:
        raise HTTPException(status_code=404, detail="Device not found")
