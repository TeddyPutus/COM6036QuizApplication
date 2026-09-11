from typing import List
from fastapi import APIRouter, status
from schemas import (
    AttemptStartRequest,
    AttemptStartResponse,
    AttemptSubmitRequest,
    AttemptResultResponse,
)

router = APIRouter(prefix="/attempts", tags=["Quiz Attempts"])


@router.post("/start", response_model=AttemptStartResponse, status_code=status.HTTP_201_CREATED)
async def start_attempt(payload: AttemptStartRequest):
    """Initialize an attempt session and lock in the server-side start timer."""
    # Delegates to ScoringService.start_attempt(user_id, payload.quiz_id)
    pass


@router.post("/{attempt_id}/submit", response_model=AttemptResultResponse)
async def submit_attempt(attempt_id: str, payload: AttemptSubmitRequest):
    """Submit student answers. Executes server-side grading and records score."""
    # Delegates to ScoringService.evaluate_submission(attempt_id, payload.answers)
    pass


@router.get("/{attempt_id}", response_model=AttemptResultResponse)
async def get_attempt_result(attempt_id: str):
    """Fetch completed attempt score, pass/fail status, and explanation breakdown."""
    # Delegates to HistoryService.get_attempt_breakdown(attempt_id)
    pass


@router.get("/history", response_model=List[AttemptResultResponse])
async def get_attempt_history():
    """Fetch past attempts and progress history for the active student."""
    # Delegates to HistoryService.get_user_history(user_id)
    pass