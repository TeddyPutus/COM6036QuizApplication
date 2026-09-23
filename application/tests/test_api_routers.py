import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from main import app
from dependencies import get_current_user
from services.auth_service import AuthService
from services.quiz_service import QuizService
from services.attempt_service import AttemptService
from services.scoring_service import ScoringService
from schemas import UserResponse, UserRole, AttemptResultResponse, AttemptStartResponse

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "tier": "application"}

from datetime import datetime, timezone
mock_student = UserResponse(id="student1", username="stu", email="s@e.com", role=UserRole.STUDENT, is_active=True, full_name="Student", created_at=datetime.now(timezone.utc))
mock_instructor = UserResponse(id="inst1", username="inst", email="i@e.com", role=UserRole.INSTRUCTOR, is_active=True, full_name="Instructor", created_at=datetime.now(timezone.utc))

# Mock services
mock_auth_service = MagicMock()
mock_quiz_service = MagicMock()
mock_attempt_service = MagicMock()
mock_scoring_service = MagicMock()

app.dependency_overrides[AuthService] = lambda: mock_auth_service
app.dependency_overrides[QuizService] = lambda: mock_quiz_service
app.dependency_overrides[AttemptService] = lambda: mock_attempt_service
app.dependency_overrides[ScoringService] = lambda: mock_scoring_service

def override_get_student():
    return mock_student

def override_get_instructor():
    return mock_instructor

# Auth Router Tests
def test_login():
    mock_auth_service.authenticate.return_value = {"access_token": "fake_token", "expires_in": 3600, "token_type": "bearer"}
    response = client.post("/api/v1/auth/login", json={"email": "s@e.com", "password": "password"})
    assert response.status_code == 200
    assert response.json()["access_token"] == "fake_token"

def test_register():
    mock_auth_service.register_user.return_value = mock_student
    response = client.post("/api/v1/auth/register", json={"email": "s@e.com", "username": "stu", "password": "password", "full_name": "Student", "role": "student"})
    assert response.status_code == 201

# Quiz Router Tests
def test_list_quizzes():
    app.dependency_overrides[get_current_user] = override_get_student
    mock_quiz_service.list_available_quizzes.return_value = []
    response = client.get("/api/v1/quizzes/")
    assert response.status_code == 200

def test_create_quiz():
    from datetime import datetime, timezone
    app.dependency_overrides[get_current_user] = override_get_instructor
    mock_quiz_service.create_quiz.return_value = {
        "id": "new_quiz", "title": "Q", "subject": "S", 
        "time_limit_minutes": 10, "passing_score_percentage": 50,
        "total_questions": 1, "is_published": False, "created_at": datetime.now(timezone.utc)
    }
    response = client.post("/api/v1/quizzes/", json={
        "title": "Q", 
        "subject": "S", 
        "time_limit_minutes": 10, 
        "passing_score_percentage": 50, 
        "questions": [
            {"prompt": "P", "points": 1, "options": [{"text": "O", "is_correct": True}, {"text": "O2", "is_correct": False}]}
        ]
    })
    assert response.status_code == 201

# Attempts Router Tests
def test_get_history():
    app.dependency_overrides[get_current_user] = override_get_student
    mock_attempt_service.get_user_history.return_value = []
    response = client.get("/api/v1/attempts/history")
    assert response.status_code == 200

def test_start_attempt():
    app.dependency_overrides[get_current_user] = override_get_student
    from datetime import datetime, timezone
    mock_scoring_service.start_attempt.return_value = AttemptStartResponse(quiz_id="q1", attempt_id="a1", started_at=datetime.now(timezone.utc), expires_at=datetime.now(timezone.utc))
    response = client.post("/api/v1/attempts/start", json={"quiz_id": "q1"})
    assert response.status_code == 201

def test_submit_attempt():
    app.dependency_overrides[get_current_user] = override_get_student
    from datetime import datetime, timezone
    mock_scoring_service.evaluate_submission.return_value = AttemptResultResponse(attempt_id="a1", quiz_id="q1", score=100.0, total_points=10, earned_points=10, passed=True, completed_at=datetime.now(timezone.utc), breakdown=[])
    response = client.post("/api/v1/attempts/a1/submit", json={"answers": []})
    assert response.status_code == 200
