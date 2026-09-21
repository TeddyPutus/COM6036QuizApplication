from datetime import datetime, timedelta, timezone
from typing import List
import uuid
from fastapi import Depends, HTTPException, status

from repositories.attempt_repo import AttemptEntity, AttemptRepository, ResponseRecordEntity
from repositories.quiz_repo import QuizRepository
from schemas import (
    AnswerSubmission,
    AttemptResultResponse,
    AttemptStartResponse,
    QuestionResultFeedback,
)


class ScoringService:
    def __init__(
        self,
        attempt_repo: AttemptRepository = Depends(AttemptRepository),
        quiz_repo: QuizRepository = Depends(QuizRepository),
    ) -> None:
        self.attempt_repo = attempt_repo
        self.quiz_repo = quiz_repo

    def start_attempt(self, user_id: str, quiz_id: str) -> AttemptStartResponse:
        quiz = self.quiz_repo.get_by_id(quiz_id)
        if not quiz or not quiz.is_published or quiz.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz not found or not available for attempts.",
            )

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=quiz.time_limit_minutes)

        attempt = AttemptEntity(
            id=str(uuid.uuid4()),
            user_id=user_id,
            quiz_id=quiz.id,
            started_at=now,
            expires_at=expires_at,
        )
        saved = self.attempt_repo.create_attempt(attempt)

        return AttemptStartResponse(
            attempt_id=saved.id,
            quiz_id=saved.quiz_id,
            started_at=saved.started_at,
            expires_at=saved.expires_at,
        )

    def evaluate_submission(
        self, user_id: str, attempt_id: str, answers: List[AnswerSubmission]
    ) -> AttemptResultResponse:
        attempt = self.attempt_repo.get_attempt_by_id(attempt_id)
        if not attempt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attempt session not found.",
            )

        if attempt.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to submit this attempt.",
            )

        if attempt.completed_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This attempt has already been submitted and graded.",
            )

        # Timer boundary: 30-second grace window to absorb network latency
        now = datetime.now(timezone.utc)
        grace_period = timedelta(seconds=30)
        if now > (attempt.expires_at + grace_period):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Submission rejected: allocated time limit expired.",
            )

        quiz = self.quiz_repo.get_by_id(attempt.quiz_id)
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Referenced quiz no longer exists.",
            )

        # Index submitted answers by question_id
        student_answers = {a.question_id: a.selected_option_id for a in answers}

        total_points = sum(q.points for q in quiz.questions)
        earned_points = 0
        response_records: List[ResponseRecordEntity] = []
        breakdown: List[QuestionResultFeedback] = []

        for question in quiz.questions:
            correct_opt = next((o for o in question.options if o.is_correct), None)
            correct_opt_id = correct_opt.id if correct_opt else ""
            correct_opt_text = correct_opt.text if correct_opt else ""

            selected_opt_id = student_answers.get(question.id, "")
            selected_opt = next((o for o in question.options if o.id == selected_opt_id), None)
            selected_opt_text = selected_opt.text if selected_opt else ""

            is_correct = bool(selected_opt_id and selected_opt_id == correct_opt_id)

            if is_correct:
                earned_points += question.points

            response_record = ResponseRecordEntity(
                id=str(uuid.uuid4()),
                attempt_id=attempt.id,
                question_id=question.id,
                prompt=question.prompt,
                selected_option_id=selected_opt_id,
                correct_option_id=correct_opt_id,
                is_correct=is_correct,
                explanation=question.explanation,
                selected_option_text=selected_opt_text,
                correct_option_text=correct_opt_text,
            )
            response_records.append(response_record)

            breakdown.append(
                QuestionResultFeedback(
                    question_id=question.id,
                    prompt=question.prompt,
                    selected_option_id=selected_opt_id,
                    correct_option_id=correct_opt_id,
                    is_correct=is_correct,
                    explanation=question.explanation,
                    selected_option_text=selected_opt_text,
                    correct_option_text=correct_opt_text,
                )
            )

        score_percentage = (earned_points / total_points * 100.0) if total_points > 0 else 0.0
        passed = score_percentage >= quiz.passing_score_percentage

        attempt.completed_at = now
        attempt.total_points = total_points
        attempt.earned_points = earned_points
        attempt.score = round(score_percentage, 2)
        attempt.passed = passed

        self.attempt_repo.save_completion(attempt, response_records)

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

    def get_attempt_result(self, user_id: str, attempt_id: str) -> AttemptResultResponse:
        attempt = self.attempt_repo.get_attempt_by_id(attempt_id)
        if not attempt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attempt record not found.",
            )

        if attempt.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to view this attempt.",
            )

        if attempt.completed_at is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Attempt is still in progress and has not been graded.",
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
