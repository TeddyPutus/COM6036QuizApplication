from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Query, status

from dependencies import get_current_user, require_instructor, require_student
from schemas import (
    QuizCreateRequest,
    QuizSummaryResponse,
    QuizTakeResponse,
    UserResponse,
)
from services.quiz_service import QuizService

router = APIRouter(prefix="/quizzes", tags=["Quizzes"])


@router.get("", response_model=List[QuizSummaryResponse])
async def list_quizzes(
    _: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[QuizService, Depends(QuizService)],
    subject: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Browse published quizzes catalog (paginated). Available to any authenticated user."""
    return service.get_catalog(subject=subject, limit=limit, offset=offset)


@router.get("/{quiz_id}/take", response_model=QuizTakeResponse)
async def get_quiz_for_taking(
    quiz_id: str,
    _: Annotated[UserResponse, Depends(require_student)],
    service: Annotated[QuizService, Depends(QuizService)],
):
    """Retrieve quiz questions and options without answer keys for a student test session."""
    return service.get_quiz_sanitized(quiz_id)


@router.post("", response_model=QuizSummaryResponse, status_code=status.HTTP_201_CREATED)
async def create_quiz(
    payload: QuizCreateRequest,
    _: Annotated[UserResponse, Depends(require_instructor)],
    service: Annotated[QuizService, Depends(QuizService)],
):
    """Instructor-only: Create a new quiz with questions and answer keys."""
    return service.create_quiz(payload)


@router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quiz(
    quiz_id: str,
    _: Annotated[UserResponse, Depends(require_instructor)],
    service: Annotated[QuizService, Depends(QuizService)],
):
    """Instructor-only: Soft delete or archive an existing quiz."""
    service.delete_quiz(quiz_id)