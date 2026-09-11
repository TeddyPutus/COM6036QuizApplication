from typing import List, Optional
from fastapi import APIRouter, Query, status
from schemas import (
    QuizCreateRequest,
    QuizSummaryResponse,
    QuizTakeResponse,
)

router = APIRouter(prefix="/quizzes", tags=["Quizzes"])


@router.get("", response_model=List[QuizSummaryResponse])
async def list_quizzes(
    subject: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Browse published quizzes catalog (paginated)."""
    # Delegates to QuizService.get_catalog(subject, limit, offset)
    pass


@router.get("/{quiz_id}/take", response_model=QuizTakeResponse)
async def get_quiz_for_taking(quiz_id: str):
    """Retrieve quiz questions and options without answer keys for a student test session."""
    # Delegates to QuizService.get_quiz_sanitized(quiz_id)
    pass


@router.post("", response_model=QuizSummaryResponse, status_code=status.HTTP_201_CREATED)
async def create_quiz(payload: QuizCreateRequest):
    """Instructor-only: Create a new quiz with questions and answer keys."""
    # Requires Instructor role; delegates to QuizService.create_quiz(payload)
    pass


@router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quiz(quiz_id: str):
    """Instructor-only: Soft delete or archive an existing quiz."""
    # Delegates to QuizService.delete_quiz(quiz_id)
    pass