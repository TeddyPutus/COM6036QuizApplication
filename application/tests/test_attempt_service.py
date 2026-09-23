import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
from datetime import datetime, timezone

from services.attempt_service import AttemptService
from schemas import UserResponse, UserRole
from repositories.attempt_repo import AttemptEntity, ResponseRecordEntity
from repositories.quiz_repo import QuizEntity

def test_get_user_history():
    mock_attempt_repo = MagicMock()
    now = datetime.now(timezone.utc)
    mock_attempt_repo.list_completed_attempts_by_user.return_value = [
        AttemptEntity(
            id="a1", user_id="u1", quiz_id="q1", score=100.0, total_points=10,
            earned_points=10, passed=True, completed_at=now, started_at=now, expires_at=now
        )
    ]
    service = AttemptService(attempt_repo=mock_attempt_repo, quiz_repo=MagicMock())
    history = service.get_user_history("u1")
    assert len(history) == 1
    assert history[0].attempt_id == "a1"
    assert history[0].score == 100.0

def test_get_attempt_detail_success_student():
    mock_attempt_repo = MagicMock()
    now = datetime.now(timezone.utc)
    mock_attempt_repo.get_attempt_by_id.return_value = AttemptEntity(
        id="a1", user_id="u1", quiz_id="q1", score=100.0, total_points=10,
        earned_points=10, passed=True, completed_at=now, started_at=now, expires_at=now
    )
    mock_attempt_repo.get_responses_for_attempt.return_value = [
        ResponseRecordEntity(
            id="r1", attempt_id="a1", question_id="q1_id", prompt="P",
            selected_option_id="o1", correct_option_id="o1", is_correct=True,
            explanation="E", selected_option_text="O", correct_option_text="O"
        )
    ]
    service = AttemptService(attempt_repo=mock_attempt_repo, quiz_repo=MagicMock())
    current_user = UserResponse(id="u1", username="stu", email="stu@e.com", role=UserRole.STUDENT, is_active=True, created_at=now, full_name="Student Name")
    
    result = service.get_attempt_detail(current_user, "a1")
    assert result.attempt_id == "a1"
    assert len(result.breakdown) == 1
    assert result.breakdown[0].is_correct is True

def test_get_attempt_detail_not_found():
    mock_attempt_repo = MagicMock()
    mock_attempt_repo.get_attempt_by_id.return_value = None
    service = AttemptService(attempt_repo=mock_attempt_repo, quiz_repo=MagicMock())
    current_user = UserResponse(id="u1", username="stu", email="stu@e.com", role=UserRole.STUDENT, is_active=True, created_at=datetime.now(timezone.utc), full_name="Student Name")
    
    with pytest.raises(HTTPException) as exc:
        service.get_attempt_detail(current_user, "a1")
    assert exc.value.status_code == 404

def test_get_attempt_detail_forbidden():
    mock_attempt_repo = MagicMock()
    now = datetime.now(timezone.utc)
    mock_attempt_repo.get_attempt_by_id.return_value = AttemptEntity(
        id="a1", user_id="u2", quiz_id="q1", score=100.0, total_points=10,
        earned_points=10, passed=True, completed_at=now, started_at=now, expires_at=now
    )
    service = AttemptService(attempt_repo=mock_attempt_repo, quiz_repo=MagicMock())
    current_user = UserResponse(id="u1", username="stu", email="stu@e.com", role=UserRole.STUDENT, is_active=True, created_at=now, full_name="Student Name")
    
    with pytest.raises(HTTPException) as exc:
        service.get_attempt_detail(current_user, "a1")
    assert exc.value.status_code == 403

def test_get_attempt_detail_active():
    mock_attempt_repo = MagicMock()
    now = datetime.now(timezone.utc)
    mock_attempt_repo.get_attempt_by_id.return_value = AttemptEntity(
        id="a1", user_id="u1", quiz_id="q1", completed_at=None, started_at=now, expires_at=now
    )
    service = AttemptService(attempt_repo=mock_attempt_repo, quiz_repo=MagicMock())
    current_user = UserResponse(id="u1", username="stu", email="stu@e.com", role=UserRole.STUDENT, is_active=True, created_at=now, full_name="Student Name")
    
    with pytest.raises(HTTPException) as exc:
        service.get_attempt_detail(current_user, "a1")
    assert exc.value.status_code == 400

def test_get_student_summary_metrics():
    mock_attempt_repo = MagicMock()
    now = datetime.now(timezone.utc)
    mock_attempt_repo.list_completed_attempts_by_user.return_value = [
        AttemptEntity(id="a1", user_id="u1", quiz_id="q1", score=100.0, passed=True, started_at=now, expires_at=now),
        AttemptEntity(id="a2", user_id="u1", quiz_id="q2", score=50.0, passed=False, started_at=now, expires_at=now)
    ]
    service = AttemptService(attempt_repo=mock_attempt_repo, quiz_repo=MagicMock())
    metrics = service.get_student_summary_metrics("u1")
    assert metrics.total_attempts == 2
    assert metrics.passed_attempts == 1
    assert metrics.average_score == 75.0
    assert metrics.pass_rate_percentage == 50.0

def test_get_student_summary_metrics_empty():
    mock_attempt_repo = MagicMock()
    mock_attempt_repo.list_completed_attempts_by_user.return_value = []
    service = AttemptService(attempt_repo=mock_attempt_repo, quiz_repo=MagicMock())
    metrics = service.get_student_summary_metrics("u1")
    assert metrics.total_attempts == 0

def test_get_quiz_attempts_for_instructor():
    mock_attempt_repo = MagicMock()
    mock_quiz_repo = MagicMock()
    
    class MockQuiz:
        id = "q1"
    
    mock_quiz_repo.get_by_id.return_value = MockQuiz()
    mock_attempt_repo.list_completed_attempts_by_quiz.return_value = [
        {
            "id": "a1", "user_id": "u1", "user_name": "stu", "user_email": "stu@e.com",
            "score": 100.0, "total_points": 10, "earned_points": 10, "passed": 1,
            "completed_at": datetime.now(timezone.utc)
        }
    ]
    service = AttemptService(attempt_repo=mock_attempt_repo, quiz_repo=mock_quiz_repo)
    results = service.get_quiz_attempts_for_instructor("q1")
    assert len(results) == 1
    assert results[0].user_name == "stu"
    assert results[0].passed is True

def test_get_quiz_attempts_for_instructor_not_found():
    mock_quiz_repo = MagicMock()
    mock_quiz_repo.get_by_id.return_value = None
    service = AttemptService(attempt_repo=MagicMock(), quiz_repo=mock_quiz_repo)
    with pytest.raises(HTTPException) as exc:
        service.get_quiz_attempts_for_instructor("q1")
    assert exc.value.status_code == 404

def test_get_quiz_metrics_for_instructor():
    mock_attempt_repo = MagicMock()
    mock_quiz_repo = MagicMock()
    
    class MockQuiz:
        id = "q1"
        title = "Quiz 1"
        
    mock_quiz_repo.get_by_id.return_value = MockQuiz()
    mock_attempt_repo.list_completed_attempts_by_quiz.return_value = [
        {"score": 100.0, "passed": 1},
        {"score": 50.0, "passed": 0}
    ]
    service = AttemptService(attempt_repo=mock_attempt_repo, quiz_repo=mock_quiz_repo)
    metrics = service.get_quiz_metrics_for_instructor("q1")
    assert metrics.total_attempts == 2
    assert metrics.passed_attempts == 1
    assert metrics.average_score == 75.0
    assert metrics.highest_score == 100.0
    assert metrics.lowest_score == 50.0

def test_get_quiz_metrics_for_instructor_empty():
    mock_attempt_repo = MagicMock()
    mock_quiz_repo = MagicMock()
    
    class MockQuiz:
        id = "q1"
        title = "Quiz 1"
        
    mock_quiz_repo.get_by_id.return_value = MockQuiz()
    mock_attempt_repo.list_completed_attempts_by_quiz.return_value = []
    service = AttemptService(attempt_repo=mock_attempt_repo, quiz_repo=mock_quiz_repo)
    metrics = service.get_quiz_metrics_for_instructor("q1")
    assert metrics.total_attempts == 0
    assert metrics.average_score == 0.0

def test_get_quiz_metrics_for_instructor_not_found():
    mock_quiz_repo = MagicMock()
    mock_quiz_repo.get_by_id.return_value = None
    service = AttemptService(attempt_repo=MagicMock(), quiz_repo=mock_quiz_repo)
    with pytest.raises(HTTPException) as exc:
        service.get_quiz_metrics_for_instructor("q1")
    assert exc.value.status_code == 404


def test_get_attempt_detail_completed_without_score():
    mock_attempt_repo = MagicMock()
    now = datetime.now(timezone.utc)
    # Edge case: Completed but score is somehow None in DB
    mock_attempt_repo.get_attempt_by_id.return_value = AttemptEntity(
        id="a1", user_id="u1", quiz_id="q1", score=None, total_points=None,
        earned_points=None, passed=None, completed_at=now, started_at=now, expires_at=now
    )
    mock_attempt_repo.get_responses_for_attempt.return_value = []
    service = AttemptService(attempt_repo=mock_attempt_repo, quiz_repo=MagicMock())
    current_user = UserResponse(id="u1", username="stu", email="stu@e.com", role=UserRole.STUDENT, is_active=True,
                                created_at=now, full_name="Student")

    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        result = service.get_attempt_detail(current_user, "a1")


def test_instructor_access_student_attempt():
    mock_attempt_repo = MagicMock()
    now = datetime.now(timezone.utc)
    mock_attempt_repo.get_attempt_by_id.return_value = AttemptEntity(
        id="a1", user_id="u2", quiz_id="q1", score=100.0, total_points=10,
        earned_points=10, passed=True, completed_at=now, started_at=now, expires_at=now
    )
    service = AttemptService(attempt_repo=mock_attempt_repo, quiz_repo=MagicMock())
    instructor = UserResponse(id="inst1", username="inst", email="i@e.com", role=UserRole.INSTRUCTOR, is_active=True,
                              created_at=now, full_name="Inst")

    # Instructor should be able to view u2's attempt
    result = service.get_attempt_detail(instructor, "a1")
    assert result.attempt_id == "a1"


def test_get_quiz_metrics_scores_none():
    mock_attempt_repo = MagicMock()
    mock_quiz_repo = MagicMock()

    class MockQuiz:
        id = "q1"
        title = "Quiz 1"

    mock_quiz_repo.get_by_id.return_value = MockQuiz()
    # Edge case: Score is None for some rows (maybe corrupted data or old scheme)
    mock_attempt_repo.list_completed_attempts_by_quiz.return_value = [
        {"score": None, "passed": 0},
        {"score": 100.0, "passed": 1}
    ]
    service = AttemptService(attempt_repo=mock_attempt_repo, quiz_repo=mock_quiz_repo)
    metrics = service.get_quiz_metrics_for_instructor("q1")
    assert metrics.total_attempts == 2
    assert metrics.passed_attempts == 1
    assert metrics.average_score == 100.0  # Only 1 valid score
    assert metrics.highest_score == 100.0


def test_get_student_summary_metrics_scores_none():
    mock_attempt_repo = MagicMock()
    now = datetime.now(timezone.utc)
    mock_attempt_repo.list_completed_attempts_by_user.return_value = [
        AttemptEntity(id="a1", user_id="u1", quiz_id="q1", score=None, passed=False, started_at=now, expires_at=now),
        AttemptEntity(id="a2", user_id="u1", quiz_id="q2", score=50.0, passed=False, started_at=now, expires_at=now)
    ]
    service = AttemptService(attempt_repo=mock_attempt_repo, quiz_repo=MagicMock())
    metrics = service.get_student_summary_metrics("u1")
    assert metrics.total_attempts == 2
    # Only 1 valid score to average (50.0 / 2 attempts)
    # 50.0 / 2 = 25.0
    assert metrics.average_score == 25.0
