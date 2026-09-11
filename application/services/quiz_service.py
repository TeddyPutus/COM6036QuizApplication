from datetime import datetime, timezone
from typing import List, Optional
import uuid
from fastapi import Depends, HTTPException, status

from repositories.quiz_repo import OptionEntity, QuestionEntity, QuizEntity, QuizRepository
from schemas import (
    QuizCreateRequest,
    QuizSummaryResponse,
    QuizTakeResponse,
    StudentOptionResponse,
    StudentQuestionResponse,
)


class QuizService:
    def __init__(self, repo: QuizRepository = Depends(QuizRepository)) -> None:
        self.repo = repo

    def get_catalog(
        self, subject: Optional[str] = None, limit: int = 20, offset: int = 0
    ) -> List[QuizSummaryResponse]:
        results = self.repo.list_catalog(subject=subject, limit=limit, offset=offset)
        return [
            QuizSummaryResponse(
                id=q.id,
                title=q.title,
                description=q.description,
                subject=q.subject,
                time_limit_minutes=q.time_limit_minutes,
                passing_score_percentage=q.passing_score_percentage,
                is_published=q.is_published,
                created_at=q.created_at,
                total_questions=count,
            )
            for q, count in results
        ]

    def get_quiz_sanitized(self, quiz_id: str) -> QuizTakeResponse:
        """Data hiding boundary: strips 'is_correct' keys and explanations for student consumption."""
        quiz = self.repo.get_by_id(quiz_id)
        if not quiz or not quiz.is_published:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz not found or currently unavailable.",
            )

        sanitized_questions = [
            StudentQuestionResponse(
                id=q.id,
                prompt=q.prompt,
                points=q.points,
                options=[
                    StudentOptionResponse(id=opt.id, text=opt.text)
                    for opt in q.options
                ],
            )
            for q in quiz.questions
        ]

        return QuizTakeResponse(
            quiz_id=quiz.id,
            title=quiz.title,
            time_limit_minutes=quiz.time_limit_minutes,
            questions=sanitized_questions,
        )

    def create_quiz(self, payload: QuizCreateRequest) -> QuizSummaryResponse:
        # Domain validation: enforce at least one correct option per question
        for idx, q in enumerate(payload.questions):
            correct_count = sum(1 for o in q.options if o.is_correct)
            if correct_count != 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Question #{idx + 1} must contain exactly one correct option.",
                )

        quiz_id = str(uuid.uuid4())
        question_entities: List[QuestionEntity] = []

        for q_in in payload.questions:
            q_id = str(uuid.uuid4())
            opt_entities = [
                OptionEntity(
                    id=str(uuid.uuid4()),
                    question_id=q_id,
                    text=opt_in.text,
                    is_correct=opt_in.is_correct,
                )
                for opt_in in q_in.options
            ]
            question_entities.append(
                QuestionEntity(
                    id=q_id,
                    quiz_id=quiz_id,
                    prompt=q_in.prompt,
                    points=q_in.points,
                    explanation=q_in.explanation,
                    options=opt_entities,
                )
            )

        new_quiz = QuizEntity(
            id=quiz_id,
            title=payload.title,
            description=payload.description,
            subject=payload.subject,
            time_limit_minutes=payload.time_limit_minutes,
            passing_score_percentage=payload.passing_score_percentage,
            is_published=True,
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            questions=question_entities,
        )

        saved = self.repo.create(new_quiz)

        return QuizSummaryResponse(
            id=saved.id,
            title=saved.title,
            description=saved.description,
            subject=saved.subject,
            time_limit_minutes=saved.time_limit_minutes,
            passing_score_percentage=saved.passing_score_percentage,
            total_questions=len(saved.questions),
            is_published=saved.is_published,
            created_at=saved.created_at,
        )

    def delete_quiz(self, quiz_id: str) -> None:
        deleted = self.repo.soft_delete(quiz_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz not found or already deleted.",
            )