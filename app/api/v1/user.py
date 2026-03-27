from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.user import UserOut, UserUpdate, UserChangePassword

from app.schemas.subscription import DeviceCreate, DeviceOut as DeviceDB
from app.services.user_service import UserService, get_user_service
from app.core.security import get_current_user
from app.models.user import User
from typing import List
from uuid import UUID

router = APIRouter(prefix="/user", tags=["User Profile"])

@router.get("/profile", response_model=UserOut)
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user

@router.patch("/profile", response_model=UserOut)
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

@router.post("/register-device", response_model=DeviceDB)
async def register_device(
    device_in: DeviceCreate,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    """
    Enregistre l'appareil actuel pour cet utilisateur.
    Utilisé pour identifier et contrôler l'accès à l'application.
    Si l'appareil existe déjà, met à jour ses informations.
    """
    return await service.register_current_device(current_user.id, device_in)


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_device(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    success = await service.remove_device(current_user.id, device_id)
    if not success:
        raise HTTPException(status_code=404, detail="Device not found")
@router.post("/change-password")
async def change_password(
    password_data: UserChangePassword,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    await service.change_password(current_user.id, password_data)
    return {"message": "Password changed successfully"}
