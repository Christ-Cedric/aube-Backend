from fastapi import APIRouter, Depends, Request
from app.schemas.user import UserCreate, UserOut, Token, UserLogin, TokenPayload
from app.services.user_service import UserService, get_user_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=UserOut, status_code=201)
async def signup(user_in: UserCreate, service: UserService = Depends(get_user_service)):
    return await service.create_user(user_in)

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    user_in: UserLogin, 
    service: UserService = Depends(get_user_service)
):
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return await service.authenticate(user_in, ip_address=ip_address, user_agent=user_agent)

@router.post("/refresh", response_model=Token)
async def refresh(
    refresh_token: str,
    service: UserService = Depends(get_user_service)
):
    return await service.refresh_token(refresh_token)

@router.post("/logout")
async def logout(
    refresh_token: str,
    service: UserService = Depends(get_user_service)
):
    await service.logout(refresh_token)
    return {"message": "Logged out successfully"}
