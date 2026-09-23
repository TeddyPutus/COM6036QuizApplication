import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from repositories.user_repo import UserRepository, UserEntity
from repositories.quiz_repo import QuizRepository, QuizEntity, QuestionEntity, OptionEntity
from repositories.attempt_repo import AttemptRepository, AttemptEntity, ResponseRecordEntity

@pytest.fixture
def mock_db_conn():
    with patch("repositories.user_repo.get_db_connection") as mock_get_user_db, \
         patch("repositories.quiz_repo.get_db_connection") as mock_get_quiz_db, \
         patch("repositories.attempt_repo.get_db_connection") as mock_get_attempt_db:
         
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # Setup context managers
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        mock_get_user_db.return_value = mock_conn
        mock_get_quiz_db.return_value = mock_conn
        mock_get_attempt_db.return_value = mock_conn
        
        yield mock_conn, mock_cursor

def test_user_repo_get_by_email(mock_db_conn):
    mock_conn, mock_cursor = mock_db_conn
    mock_cursor.fetchone.return_value = {
        "id": "u1", "email": "test@e.com", "full_name": "Test", 
        "role": "student", "hashed_password": "hash", "created_at": datetime.now(timezone.utc)
    }
    
    repo = UserRepository()
    user = repo.get_by_email("test@e.com")
    assert user.id == "u1"
    assert user.email == "test@e.com"
    mock_cursor.execute.assert_called_with(
        "SELECT * FROM users WHERE LOWER(email) = LOWER(%s)", ("test@e.com",)
    )

def test_user_repo_create(mock_db_conn):
    mock_conn, mock_cursor = mock_db_conn
    repo = UserRepository()
    
    user = UserEntity(id="u1", email="e@e", full_name="n", role="student", hashed_password="h", created_at=datetime.now(timezone.utc))
    repo.create(user)
    
    assert mock_cursor.execute.call_count > 0

def test_quiz_repo_get_by_id(mock_db_conn):
    mock_conn, mock_cursor = mock_db_conn
    mock_cursor.fetchone.return_value = {
        "id": "q1", "title": "T", "description": "D", "subject": "S",
        "time_limit_minutes": 10, "passing_score_percentage": 50,
        "is_published": True, "is_deleted": False, "created_at": datetime.now(timezone.utc)
    }
    mock_cursor.fetchall.side_effect = [
        # Questions
        [{"id": "q1_id", "quiz_id": "q1", "prompt": "P", "explanation": "E", "points": 1}],
        # Options
        [{"id": "o1", "question_id": "q1_id", "text": "O", "is_correct": True}]
    ]
    
    repo = QuizRepository()
    quiz = repo.get_by_id("q1")
    assert quiz.id == "q1"
    assert len(quiz.questions) == 1
    assert len(quiz.questions[0].options) == 1

def test_quiz_repo_create(mock_db_conn):
    mock_conn, mock_cursor = mock_db_conn
    repo = QuizRepository()
    
    quiz = QuizEntity(
        id="q1", title="T", description="D", subject="S", time_limit_minutes=10, 
        passing_score_percentage=50, is_published=True, is_deleted=False, 
        created_at=datetime.now(timezone.utc),
        questions=[
            QuestionEntity(id="q1_id", quiz_id="q1", prompt="P", explanation="E", points=1, options=[
                OptionEntity(id="o1", question_id="q1_id", text="O", is_correct=True)
            ])
        ]
    )
    repo.create(quiz)
    assert mock_cursor.execute.call_count > 0

def test_attempt_repo_get_by_id(mock_db_conn):
    mock_conn, mock_cursor = mock_db_conn
    mock_cursor.fetchone.return_value = {
        "id": "a1", "user_id": "u1", "quiz_id": "q1", "started_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc), "completed_at": None,
        "score": None, "total_points": None, "earned_points": None, "passed": None
    }
    repo = AttemptRepository()
    attempt = repo.get_attempt_by_id("a1")
    assert attempt.id == "a1"

def test_attempt_repo_create(mock_db_conn):
    mock_conn, mock_cursor = mock_db_conn
    repo = AttemptRepository()
    attempt = AttemptEntity(
        id="a1", user_id="u1", quiz_id="q1", started_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc)
    )
    repo.create_attempt(attempt)
    assert mock_cursor.execute.call_count > 0

def test_attempt_repo_save_completion(mock_db_conn):
    mock_conn, mock_cursor = mock_db_conn
    repo = AttemptRepository()
    attempt = AttemptEntity(
        id="a1", user_id="u1", quiz_id="q1", started_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc),
        score=100.0, total_points=10, earned_points=10, passed=True
    )
    responses = [
        ResponseRecordEntity(
            id="r1", attempt_id="a1", question_id="q_id", prompt="P",
            selected_option_id="o1", selected_option_text="O",
            correct_option_id="o1", correct_option_text="O",
            is_correct=True, explanation="E"
        )
    ]
    repo.save_completion(attempt, responses)
    assert mock_cursor.execute.call_count > 0
