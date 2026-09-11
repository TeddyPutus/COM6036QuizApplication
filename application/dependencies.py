# dependencies.py
from typing import Annotated, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

from schemas import UserResponse, UserRole
from utils.security import decode_access_token
from services.auth_service import AuthService

security_scheme = HTTPBearer()


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_scheme)],
    service: Annotated[AuthService, Depends(AuthService)],
) -> UserResponse:
    """Extracts, verifies JWT token, and returns the active user entity."""
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload: missing subject identifier.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return service.get_user_by_id(user_id)


def require_role(*allowed_roles: UserRole) -> Callable[[UserResponse], UserResponse]:
    """Factory dependency that restricts access to specific user roles."""
    def role_checker(
        current_user: Annotated[UserResponse, Depends(get_current_user)]
    ) -> UserResponse:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required roles: {[r.value for r in allowed_roles]}",
            )
        return current_user

    return role_checker


require_student = require_role(UserRole.STUDENT)
require_instructor = require_role(UserRole.INSTRUCTOR, UserRole.ADMIN)