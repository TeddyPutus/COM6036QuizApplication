from fastapi import APIRouter, status
from schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegisterRequest):
    """Register a new user account."""
    # Delegates to AuthService.register_user(payload)
    pass


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLoginRequest):
    """Authenticate and obtain JWT bearer token."""
    # Delegates to AuthService.authenticate(payload.email, payload.password)
    pass


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile():
    """Return profile for the currently authenticated session."""
    # Decoded from JWT via auth middleware dependency
    pass