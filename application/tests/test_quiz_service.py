import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
from datetime import datetime, timezone

from services.quiz_service import QuizService
from schemas import QuizCreateRequest, QuestionCreate, OptionCreate
from repositories.quiz_repo import QuizEntity, QuestionEntity, OptionEntity

def test_create_quiz_success():
    mock_repo = MagicMock()
    mock_repo.create.side_effect = lambda entity: entity

    service = QuizService(repo=mock_repo)
    
    payload = QuizCreateRequest(
        title="Test Quiz",
        subject="Testing",
        time_limit_minutes=30,
        passing_score_percentage=60,
        questions=[
            QuestionCreate(
                prompt="Is this a test?",
                points=1,
                options=[
                    OptionCreate(text="Yes", is_correct=True),
                    OptionCreate(text="No", is_correct=False)
                ]
            )
        ]
    )
    
    result = service.create_quiz(payload)
    assert result.title == "Test Quiz"
    assert result.total_questions == 1
    mock_repo.create.assert_called_once()

def test_create_quiz_invalid_options():
    mock_repo = MagicMock()
    service = QuizService(repo=mock_repo)
    
    # 0 correct options
    payload = QuizCreateRequest(
        title="Bad Quiz",
        subject="Testing",
        time_limit_minutes=10,
        passing_score_percentage=50,
        questions=[
            QuestionCreate(
                prompt="Is this a test?",
                points=1,
                options=[
                    OptionCreate(text="Yes", is_correct=False),
                    OptionCreate(text="No", is_correct=False)
                ]
            )
        ]
    )
    
    with pytest.raises(HTTPException) as exc_info:
        service.create_quiz(payload)
    
    assert exc_info.value.status_code == 400
    assert "exactly one correct option" in exc_info.value.detail

def test_create_quiz_identical_options():
    mock_repo = MagicMock()
    service = QuizService(repo=mock_repo)
    
    # 2 identical options (case/space differences)
    payload = QuizCreateRequest(
        title="Bad Quiz 2",
        subject="Testing",
        time_limit_minutes=10,
        passing_score_percentage=50,
        questions=[
            QuestionCreate(
                prompt="Is this a test?",
                points=1,
                options=[
                    OptionCreate(text=" Yes ", is_correct=True),
                    OptionCreate(text="yes", is_correct=False)
                ]
            )
        ]
    )
    
    with pytest.raises(HTTPException) as exc_info:
        service.create_quiz(payload)
    
    assert exc_info.value.status_code == 400
    assert "at least two distinct options" in exc_info.value.detail

def test_get_quiz_sanitized_success():
    mock_repo = MagicMock()
    service = QuizService(repo=mock_repo)
    
    # Setup mock quiz with answers
    opt1 = OptionEntity(id="opt1", question_id="q1", text="A", is_correct=True)
    opt2 = OptionEntity(id="opt2", question_id="q1", text="B", is_correct=False)
    q1 = QuestionEntity(id="q1", quiz_id="quiz1", prompt="What?", points=10, options=[opt1, opt2])
    
    mock_repo.get_by_id.return_value = QuizEntity(
        id="quiz1", title="Sanitized", description="", subject="Test",
        time_limit_minutes=15, passing_score_percentage=50, is_published=True, is_deleted=False,
        created_at=datetime.now(timezone.utc), questions=[q1]
    )
    
    result = service.get_quiz_sanitized("quiz1")
    
    assert result.title == "Sanitized"
    assert len(result.questions) == 1
    # Check that answers are stripped out from the student schema
    assert hasattr(result.questions[0].options[0], "is_correct") is False
    assert result.questions[0].options[0].text == "A"

def test_delete_quiz_success():
    mock_repo = MagicMock()
    mock_repo.soft_delete.return_value = True
    service = QuizService(repo=mock_repo)
    
    service.delete_quiz("quiz1")
    mock_repo.soft_delete.assert_called_once_with("quiz1")

def test_delete_quiz_not_found():
    mock_repo = MagicMock()
    mock_repo.soft_delete.return_value = False
    service = QuizService(repo=mock_repo)
    
    with pytest.raises(HTTPException) as exc_info:
        service.delete_quiz("quiz1")
        
    assert exc_info.value.status_code == 404
