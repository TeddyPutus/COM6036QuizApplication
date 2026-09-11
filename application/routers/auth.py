from fastapi import APIRouter, status, Depends

from dependencies import get_current_user
from schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
)
from services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserRegisterRequest,
    service: AuthService = Depends(AuthService),
):
    """Register a new user account."""
    return service.register_user(payload)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: UserLoginRequest,
    service: AuthService = Depends(AuthService),
):
    """Authenticate and obtain JWT bearer token."""
    return service.authenticate(payload)


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: UserResponse = Depends(get_current_user),
):
    """Return profile for the currently authenticated session."""
    return current_user