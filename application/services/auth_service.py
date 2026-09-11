from datetime import datetime, timezone
import uuid
from fastapi import HTTPException, status, Depends

from repositories.user_repo import UserEntity, UserRepository
from schemas import TokenResponse, UserLoginRequest, UserRegisterRequest, UserResponse, UserRole
from utils.security import create_access_token, hash_password, verify_password


class AuthService:
    def __init__(self, repo: UserRepository = Depends(UserRepository)) -> None:
        self.repo = repo

    def register_user(self, payload: UserRegisterRequest) -> UserResponse:
        existing_user = self.repo.get_by_email(payload.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email address already exists.",
            )

        new_user = UserEntity(
            id=str(uuid.uuid4()),
            email=payload.email,
            full_name=payload.full_name,
            role=payload.role.value,
            hashed_password=hash_password(payload.password),
            created_at=datetime.now(timezone.utc),
        )

        saved = self.repo.create(new_user)
        return UserResponse(
            id=saved.id,
            email=saved.email,
            full_name=saved.full_name,
            role=UserRole(saved.role),
            created_at=saved.created_at,
        )

    def authenticate(self, payload: UserLoginRequest) -> TokenResponse:
        user = self.repo.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token, expires_in = create_access_token(
            payload={"sub": user.id, "email": user.email, "role": user.role}
        )

        return TokenResponse(access_token=token, token_type="bearer", expires_in=expires_in)

    def get_user_by_id(self, user_id: str) -> UserResponse:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User account not found.",
            )
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=UserRole(user.role),
            created_at=user.created_at,
        )


auth_service = AuthService()