# routers/attempts.py
from typing import Annotated, List
from fastapi import APIRouter, Depends, status

from dependencies import get_current_user, require_instructor, require_student
from schemas import (
    AttemptResultResponse,
    AttemptStartRequest,
    AttemptStartResponse,
    AttemptSubmitRequest,
    InstructorAttemptResponse,
    QuizAnalyticsSummary,
    UserResponse,
)
from services.attempt_service import AttemptService, StudentAnalyticsSummary
from services.scoring_service import ScoringService

router = APIRouter(
    prefix="/attempts",
    tags=["Quiz Attempts & History"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/start", response_model=AttemptStartResponse, status_code=status.HTTP_201_CREATED)
async def start_attempt(
    payload: AttemptStartRequest,
    current_user: Annotated[UserResponse, Depends(require_student)],
    service: Annotated[ScoringService, Depends(ScoringService)],
):
    return service.start_attempt(user_id=current_user.id, quiz_id=payload.quiz_id)


@router.post("/{attempt_id}/submit", response_model=AttemptResultResponse)
async def submit_attempt(
    attempt_id: str,
    payload: AttemptSubmitRequest,
    current_user: Annotated[UserResponse, Depends(require_student)],
    service: Annotated[ScoringService, Depends(ScoringService)],
):
    return service.evaluate_submission(
        user_id=current_user.id, attempt_id=attempt_id, answers=payload.answers
    )


@router.get("/history", response_model=List[AttemptResultResponse])
async def get_attempt_history(
    current_user: Annotated[UserResponse, Depends(require_student)],
    attempt_service: Annotated[AttemptService, Depends(AttemptService)],
):
    return attempt_service.get_user_history(user_id=current_user.id)


@router.get("/metrics", response_model=StudentAnalyticsSummary)
async def get_student_metrics(
    current_user: Annotated[UserResponse, Depends(require_student)],
    attempt_service: Annotated[AttemptService, Depends(AttemptService)],
):
    return attempt_service.get_student_summary_metrics(user_id=current_user.id)


# --- Instructor-Only Endpoints ---

@router.get("/quiz/{quiz_id}", response_model=List[InstructorAttemptResponse])
async def get_quiz_attempts_for_instructor(
    quiz_id: str,
    instructor: Annotated[UserResponse, Depends(require_instructor)],
    attempt_service: Annotated[AttemptService, Depends(AttemptService)],
):
    """Instructor-only: View list of completed attempts and student scores for a quiz."""
    return attempt_service.get_quiz_attempts_for_instructor(quiz_id=quiz_id)


@router.get("/quiz/{quiz_id}/metrics", response_model=QuizAnalyticsSummary)
async def get_quiz_metrics_for_instructor(
    quiz_id: str,
    instructor: Annotated[UserResponse, Depends(require_instructor)],
    attempt_service: Annotated[AttemptService, Depends(AttemptService)],
):
    """Instructor-only: Retrieve aggregate statistics (average, pass rate, score extremes)."""
    return attempt_service.get_quiz_metrics_for_instructor(quiz_id=quiz_id)


# --- Dynamic Attempt Detail Route ---

@router.get("/{attempt_id}", response_model=AttemptResultResponse)
async def get_attempt_result(
    attempt_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    attempt_service: Annotated[AttemptService, Depends(AttemptService)],
):
    return attempt_service.get_attempt_detail(current_user=current_user, attempt_id=attempt_id)