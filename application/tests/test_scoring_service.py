import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
from datetime import datetime, timedelta, timezone

from services.scoring_service import ScoringService
from schemas import AnswerSubmission
from repositories.attempt_repo import AttemptEntity
from repositories.quiz_repo import QuizEntity

# Mock classes for Quiz entities
class MockOption:
    def __init__(self, id, is_correct):
        self.id = id
        self.is_correct = is_correct
        self.text = "Option Text"

class MockQuestion:
    def __init__(self, id, points, options):
        self.id = id
        self.points = points
        self.options = options
        self.prompt = "Question Prompt"
        self.explanation = "Explanation"

class MockQuiz:
    def __init__(self, id, is_published, is_deleted, time_limit_minutes, passing_score_percentage, questions):
        self.id = id
        self.is_published = is_published
        self.is_deleted = is_deleted
        self.time_limit_minutes = time_limit_minutes
        self.passing_score_percentage = passing_score_percentage
        self.questions = questions


def test_start_attempt_success():
    mock_attempt_repo = MagicMock()
    mock_quiz_repo = MagicMock()
    
    # Mock Quiz
    mock_quiz_repo.get_by_id.return_value = MockQuiz(
        id="q1", is_published=True, is_deleted=False, time_limit_minutes=30, passing_score_percentage=50, questions=[]
    )
    
    mock_attempt_repo.create_attempt.side_effect = lambda entity: entity
    
    service = ScoringService(attempt_repo=mock_attempt_repo, quiz_repo=mock_quiz_repo)
    
    response = service.start_attempt(user_id="u1", quiz_id="q1")
    
    assert response.quiz_id == "q1"
    assert response.attempt_id is not None
    # Check that expiry is roughly 30 mins in the future
    diff = response.expires_at - response.started_at
    assert diff.total_seconds() == 30 * 60
    
    mock_quiz_repo.get_by_id.assert_called_once_with("q1")
    mock_attempt_repo.create_attempt.assert_called_once()


def test_start_attempt_quiz_not_published():
    mock_attempt_repo = MagicMock()
    mock_quiz_repo = MagicMock()
    
    mock_quiz_repo.get_by_id.return_value = MockQuiz(
        id="q1", is_published=False, is_deleted=False, time_limit_minutes=30, passing_score_percentage=50, questions=[]
    )
    
    service = ScoringService(attempt_repo=mock_attempt_repo, quiz_repo=mock_quiz_repo)
    
    with pytest.raises(HTTPException) as exc_info:
        service.start_attempt(user_id="u1", quiz_id="q1")
        
    assert exc_info.value.status_code == 404
    assert "not available" in exc_info.value.detail


def test_evaluate_submission_success():
    mock_attempt_repo = MagicMock()
    mock_quiz_repo = MagicMock()
    
    # Mock active attempt
    now = datetime.now(timezone.utc)
    mock_attempt_repo.get_attempt_by_id.return_value = AttemptEntity(
        id="a1", user_id="u1", quiz_id="q1", started_at=now - timedelta(minutes=5), expires_at=now + timedelta(minutes=25)
    )
    
    # Mock Quiz with 1 question, 1 point
    q1 = MockQuestion(id="q1_id", points=10, options=[
        MockOption(id="opt1", is_correct=True),
        MockOption(id="opt2", is_correct=False)
    ])
    mock_quiz_repo.get_by_id.return_value = MockQuiz(
        id="q1", is_published=True, is_deleted=False, time_limit_minutes=30, passing_score_percentage=50, questions=[q1]
    )
    
    service = ScoringService(attempt_repo=mock_attempt_repo, quiz_repo=mock_quiz_repo)
    
    answers = [AnswerSubmission(question_id="q1_id", selected_option_id="opt1")]
    
    result = service.evaluate_submission(user_id="u1", attempt_id="a1", answers=answers)
    
    assert result.score == 100.0
    assert result.passed is True
    assert result.earned_points == 10
    assert result.total_points == 10
    mock_attempt_repo.save_completion.assert_called_once()


def test_evaluate_submission_expired_time():
    mock_attempt_repo = MagicMock()
    mock_quiz_repo = MagicMock()
    
    # Mock attempt expired 10 minutes ago
    now = datetime.now(timezone.utc)
    mock_attempt_repo.get_attempt_by_id.return_value = AttemptEntity(
        id="a1", user_id="u1", quiz_id="q1", started_at=now - timedelta(minutes=40), expires_at=now - timedelta(minutes=10)
    )
    
    service = ScoringService(attempt_repo=mock_attempt_repo, quiz_repo=mock_quiz_repo)
    
    with pytest.raises(HTTPException) as exc_info:
        service.evaluate_submission(user_id="u1", attempt_id="a1", answers=[])
        
    assert exc_info.value.status_code == 400
    assert "time limit expired" in exc_info.value.detail


def test_evaluate_submission_already_completed():
    mock_attempt_repo = MagicMock()
    mock_quiz_repo = MagicMock()
    now = datetime.now(timezone.utc)
    mock_attempt_repo.get_attempt_by_id.return_value = AttemptEntity(
        id='a1', user_id='u1', quiz_id='q1', started_at=now - timedelta(minutes=5), expires_at=now + timedelta(minutes=25), completed_at=now
    )
    service = ScoringService(attempt_repo=mock_attempt_repo, quiz_repo=mock_quiz_repo)
    with pytest.raises(HTTPException) as exc_info:
        service.evaluate_submission(user_id='u1', attempt_id='a1', answers=[])
    assert exc_info.value.status_code == 400
    assert 'already been submitted' in exc_info.value.detail

def test_evaluate_submission_partial_answers():
    mock_attempt_repo = MagicMock()
    mock_quiz_repo = MagicMock()
    now = datetime.now(timezone.utc)
    mock_attempt_repo.get_attempt_by_id.return_value = AttemptEntity(
        id='a1', user_id='u1', quiz_id='q1', started_at=now, expires_at=now + timedelta(minutes=25)
    )
    q1 = MockQuestion(id='q1_id', points=5, options=[MockOption(id='opt1', is_correct=True)])
    q2 = MockQuestion(id='q2_id', points=5, options=[MockOption(id='opt2', is_correct=True)])
    mock_quiz_repo.get_by_id.return_value = MockQuiz(
        id='q1', is_published=True, is_deleted=False, time_limit_minutes=30, passing_score_percentage=50, questions=[q1, q2]
    )
    service = ScoringService(attempt_repo=mock_attempt_repo, quiz_repo=mock_quiz_repo)
    answers = [AnswerSubmission(question_id='q1_id', selected_option_id='opt1')] # Missing q2 answer
    result = service.evaluate_submission(user_id='u1', attempt_id='a1', answers=answers)
    assert result.earned_points == 5
    assert result.total_points == 10
    assert result.score == 50.0

