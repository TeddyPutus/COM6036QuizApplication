# services/history_service.py
from datetime import datetime
from typing import List, Optional
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel

from repositories.attempt_repo import AttemptRepository
from repositories.quiz_repo import QuizRepository
from schemas import (
    AttemptResultResponse,
    InstructorAttemptResponse,
    QuestionResultFeedback,
    QuizAnalyticsSummary,
    UserResponse,
    UserRole,
)


class StudentAnalyticsSummary(BaseModel):
    total_attempts: int
    passed_attempts: int
    average_score: float
    pass_rate_percentage: float


class AttemptService:
    """Domain service responsible for progress tracking, attempt reviews, and analytics."""

    def __init__(
        self,
        attempt_repo: AttemptRepository = Depends(AttemptRepository),
        quiz_repo: QuizRepository = Depends(QuizRepository),
    ) -> None:
        self.attempt_repo = attempt_repo
        self.quiz_repo = quiz_repo

    def get_user_history(self, user_id: str) -> List[AttemptResultResponse]:
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
                breakdown=None,
            )
            for a in attempts
        ]

    def get_attempt_detail(
        self, current_user: UserResponse, attempt_id: str
    ) -> AttemptResultResponse:
        attempt = self.attempt_repo.get_attempt_by_id(attempt_id)
        if not attempt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attempt record not found.",
            )

        # Allow access if the user is an Instructor/Admin OR the student who took it
        is_staff = current_user.role in [UserRole.INSTRUCTOR, UserRole.ADMIN]
        if not is_staff and attempt.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You cannot view this attempt.",
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

    def get_quiz_attempts_for_instructor(
        self, quiz_id: str
    ) -> List[InstructorAttemptResponse]:
        """Returns every completed student attempt for a given quiz."""
        quiz = self.quiz_repo.get_by_id(quiz_id)
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz not found.",
            )

        rows = self.attempt_repo.list_completed_attempts_by_quiz(quiz_id)
        return [
            InstructorAttemptResponse(
                attempt_id=r["id"],
                user_id=r["user_id"],
                user_name=r["user_name"],
                user_email=r["user_email"],
                score=r["score"],
                total_points=r["total_points"],
                earned_points=r["earned_points"],
                passed=bool(r["passed"]),
                completed_at=r["completed_at"],
            )
            for r in rows
        ]

    def get_quiz_metrics_for_instructor(self, quiz_id: str) -> QuizAnalyticsSummary:
        """Calculates aggregate metrics (average, pass rate, high, low) for an instructor."""
        quiz = self.quiz_repo.get_by_id(quiz_id)
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz not found.",
            )

        rows = self.attempt_repo.list_completed_attempts_by_quiz(quiz_id)
        total = len(rows)

        if total == 0:
            return QuizAnalyticsSummary(
                quiz_id=quiz.id,
                quiz_title=quiz.title,
                total_attempts=0,
                passed_attempts=0,
                pass_rate_percentage=0.0,
                average_score=0.0,
                highest_score=0.0,
                lowest_score=0.0,
            )

        scores = [float(r["score"]) for r in rows if r["score"] is not None]
        passed_count = sum(1 for r in rows if r["passed"])
        avg_score = sum(scores) / len(scores) if scores else 0.0

        return QuizAnalyticsSummary(
            quiz_id=quiz.id,
            quiz_title=quiz.title,
            total_attempts=total,
            passed_attempts=passed_count,
            pass_rate_percentage=round((passed_count / total) * 100.0, 2),
            average_score=round(avg_score, 2),
            highest_score=round(max(scores), 2) if scores else 0.0,
            lowest_score=round(min(scores), 2) if scores else 0.0,
        )