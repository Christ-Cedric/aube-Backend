from fastapi import APIRouter, Depends
from app.models.auth import UserSignup, UserLogin, Token
from app.models.user import User
from app.services.user_service import UserService, get_user_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=User, status_code=201)
async def signup(user_in: UserSignup, service: UserService = Depends(get_user_service)):
    """
    Register a new user.
    """
    return await service.create_user(user_in)

@router.post("/login", response_model=Token)
async def login(user_in: UserLogin, service: UserService = Depends(get_user_service)):
    """
    Authenticate user and return JWT access token.
    """
    return await service.authenticate(user_in)
