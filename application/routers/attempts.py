# routers/attempts.py
from typing import Annotated, List
from fastapi import APIRouter, Depends, status

from dependencies import get_current_user
from schemas import (
    AttemptResultResponse,
    AttemptStartRequest,
    AttemptStartResponse,
    AttemptSubmitRequest,
    UserResponse,
)
from services.attempt_service import AttemptService, StudentAnalyticsSummary
from services.scoring_service import ScoringService

router = APIRouter(
    prefix="/attempts",
    tags=["Quiz Attempts & History"],
    dependencies=[Depends(get_current_user)],
)

# --- Write Operations (Delegated to AttemptService) ---

@router.post("/start", response_model=AttemptStartResponse, status_code=status.HTTP_201_CREATED)
async def start_attempt(
    payload: AttemptStartRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[ScoringService, Depends(ScoringService)],
):
    return service.start_attempt(user_id=current_user.id, quiz_id=payload.quiz_id)


@router.post("/{attempt_id}/submit", response_model=AttemptResultResponse)
async def submit_attempt(
    attempt_id: str,
    payload: AttemptSubmitRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[ScoringService, Depends(ScoringService)],
):
    return service.evaluate_submission(
        user_id=current_user.id, attempt_id=attempt_id, answers=payload.answers
    )


# --- Read & Review Operations (Delegated to HistoryService) ---

@router.get("/history", response_model=List[AttemptResultResponse])
async def get_attempt_history(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    history_service: Annotated[AttemptService, Depends(AttemptService)],
):
    """Retrieve all past quiz attempts for the logged-in student."""
    return history_service.get_user_history(user_id=current_user.id)


@router.get("/metrics", response_model=StudentAnalyticsSummary)
async def get_student_metrics(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    history_service: Annotated[AttemptService, Depends(AttemptService)],
):
    """Retrieve aggregate performance indicators (pass rate, average score)."""
    return history_service.get_student_summary_metrics(user_id=current_user.id)


@router.get("/{attempt_id}", response_model=AttemptResultResponse)
async def get_attempt_result(
    attempt_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    history_service: Annotated[AttemptService, Depends(AttemptService)],
):
    """Retrieve complete answer-by-answer breakdown for a finished attempt."""
    return history_service.get_attempt_detail(user_id=current_user.id, attempt_id=attempt_id)