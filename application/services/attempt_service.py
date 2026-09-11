# services/attempt_service.py
from typing import List, Optional
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel

from repositories.attempt_repo import AttemptRepository
from schemas import AttemptResultResponse, QuestionResultFeedback


class StudentAnalyticsSummary(BaseModel):
    total_attempts: int
    passed_attempts: int
    average_score: float
    pass_rate_percentage: float


class AttemptService:
    """Domain service responsible for progress tracking, attempt reviews, and analytics."""

    def __init__(self, attempt_repo: AttemptRepository = Depends(AttemptRepository)) -> None:
        self.attempt_repo = attempt_repo

    def get_user_history(self, user_id: str) -> List[AttemptResultResponse]:
        """Fetches lightweight summaries of all completed quizzes for a student."""
        attempts = self.attempt_repo.list_completed_attempts_by_user(user_id)
        return [
            AttemptResultResponse(
                attempt_id=a.id,
                quiz_id=a.quiz_id,
                score=a.score,
                total_points=a.total_points,
                earned_points=a.earned_points,
                passed=a.passed,
                completed_at=a.completed_at,
                breakdown=None,  # Breakdown omitted in list view to reduce network payload
            )
            for a in attempts
        ]

    def get_attempt_detail(self, user_id: str, attempt_id: str) -> AttemptResultResponse:
        """Retrieves an in-depth audit of a specific attempt with per-question rationale."""
        attempt = self.attempt_repo.get_attempt_by_id(attempt_id)
        if not attempt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attempt record not found.",
            )

        if attempt.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You cannot view another student's test history.",
            )

        if attempt.completed_at is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This attempt is still active and cannot be reviewed until submitted.",
            )

        responses = self.attempt_repo.get_responses_for_attempt(attempt.id)
        breakdown = [
            QuestionResultFeedback(
                question_id=r.question_id,
                prompt=r.prompt,
                selected_option_id=r.selected_option_id,
                correct_option_id=r.correct_option_id,
                is_correct=r.is_correct,
                explanation=r.explanation,
            )
            for r in responses
        ]

        return AttemptResultResponse(
            attempt_id=attempt.id,
            quiz_id=attempt.quiz_id,
            score=attempt.score,
            total_points=attempt.total_points,
            earned_points=attempt.earned_points,
            passed=attempt.passed,
            completed_at=attempt.completed_at,
            breakdown=breakdown,
        )

    def get_student_summary_metrics(self, user_id: str) -> StudentAnalyticsSummary:
        """Innovation metric: aggregates long-term diagnostic learning progress."""
        attempts = self.attempt_repo.list_completed_attempts_by_user(user_id)
        if not attempts:
            return StudentAnalyticsSummary(
                total_attempts=0, passed_attempts=0, average_score=0.0, pass_rate_percentage=0.0
            )

        total = len(attempts)
        passed = sum(1 for a in attempts if a.passed)
        avg_score = sum(a.score for a in attempts if a.score is not None) / total

        return StudentAnalyticsSummary(
            total_attempts=total,
            passed_attempts=passed,
            average_score=round(avg_score, 2),
            pass_rate_percentage=round((passed / total) * 100.0, 2),
        )