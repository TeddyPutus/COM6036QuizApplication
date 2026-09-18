import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
from datetime import datetime, timezone

from services.auth_service import AuthService
from schemas import UserRegisterRequest, UserLoginRequest, UserRole
from repositories.user_repo import UserEntity
from utils.security import hash_password

def test_register_user_success():
    mock_repo = MagicMock()
    mock_repo.get_by_email.return_value = None
    
    # Mock create to just return the passed entity
    mock_repo.create.side_effect = lambda entity: entity

    service = AuthService(repo=mock_repo)
    
    payload = UserRegisterRequest(
        email="test@example.com",
        password="password123",
        full_name="Test User",
        role=UserRole.STUDENT
    )
    
    response = service.register_user(payload)
    
    assert response.email == "test@example.com"
    assert response.full_name == "Test User"
    assert response.role == UserRole.STUDENT
    mock_repo.create.assert_called_once()


def test_register_user_existing_email():
    mock_repo = MagicMock()
    # Simulate existing user
    mock_repo.get_by_email.return_value = UserEntity(
        id="123", email="test@example.com", full_name="Old", role="student", hashed_password="abc", created_at=datetime.now(timezone.utc)
    )

    service = AuthService(repo=mock_repo)
    
    payload = UserRegisterRequest(
        email="test@example.com",
        password="password123",
        full_name="Test User",
        role=UserRole.STUDENT
    )
    
    with pytest.raises(HTTPException) as exc_info:
        service.register_user(payload)
        
    assert exc_info.value.status_code == 409
    assert "already exists" in exc_info.value.detail


def test_authenticate_success():
    mock_repo = MagicMock()
    # Simulate existing user with hashed password
    hashed_pw = hash_password("password123")
    mock_repo.get_by_email.return_value = UserEntity(
        id="123", email="test@example.com", full_name="Test", role="student", hashed_password=hashed_pw, created_at=datetime.now(timezone.utc)
    )

    service = AuthService(repo=mock_repo)
    
    payload = UserLoginRequest(
        email="test@example.com",
        password="password123"
    )
    
    response = service.authenticate(payload)
    assert response.access_token is not None
    assert response.token_type == "bearer"


def test_authenticate_wrong_password():
    mock_repo = MagicMock()
    hashed_pw = hash_password("password123")
    mock_repo.get_by_email.return_value = UserEntity(
        id="123", email="test@example.com", full_name="Test", role="student", hashed_password=hashed_pw, created_at=datetime.now(timezone.utc)
    )

    service = AuthService(repo=mock_repo)
    
    payload = UserLoginRequest(
        email="test@example.com",
        password="wrongpassword"
    )
    
    with pytest.raises(HTTPException) as exc_info:
        service.authenticate(payload)
        
    assert exc_info.value.status_code == 401
    assert "Invalid email or password" in exc_info.value.detail
