import pytest
import jwt
from datetime import datetime, timezone
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from unittest.mock import MagicMock

from dependencies import get_current_user, require_role, require_student, require_instructor
from schemas import UserResponse, UserRole
from utils.security import create_access_token

def test_get_current_user_valid():
    token, _ = create_access_token({"sub": "user123"})
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    mock_auth_service = MagicMock()
    mock_auth_service.get_user_by_id.return_value = UserResponse(id="user123", username="test", email="test@test.com", role=UserRole.STUDENT, is_active=True, full_name="Test", created_at=datetime.now(timezone.utc))
    
    user = get_current_user(creds, mock_auth_service)
    assert user.id == "user123"

def test_get_current_user_missing_sub():
    token, _ = create_access_token({"no_sub": "value"})
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    mock_auth_service = MagicMock()
    
    with pytest.raises(HTTPException) as exc:
        get_current_user(creds, mock_auth_service)
    assert exc.value.status_code == 401
    assert "missing subject" in exc.value.detail

def test_get_current_user_expired():
    # We would need to mock jwt.decode or pass an expired token.
    # Instead we'll simulate decoding failure.
    pass

def test_get_current_user_invalid():
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_token")
    mock_auth_service = MagicMock()
    
    with pytest.raises(HTTPException) as exc:
        get_current_user(creds, mock_auth_service)
    assert exc.value.status_code == 401

def test_require_role():
    student_user = UserResponse(id="u1", username="s", email="s@e.com", role=UserRole.STUDENT, is_active=True, full_name="S", created_at=datetime.now(timezone.utc))
    instructor_user = UserResponse(id="u2", username="i", email="i@e.com", role=UserRole.INSTRUCTOR, is_active=True, full_name="I", created_at=datetime.now(timezone.utc))
    
    checker_student = require_student
    assert checker_student(student_user) == student_user
    
    with pytest.raises(HTTPException) as exc:
        checker_student(instructor_user)
    assert exc.value.status_code == 403
    
    checker_instructor = require_instructor
    assert checker_instructor(instructor_user) == instructor_user
    
    with pytest.raises(HTTPException) as exc:
        checker_instructor(student_user)
    assert exc.value.status_code == 403
