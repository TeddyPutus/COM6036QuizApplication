# repositories/attempt_repo.py
from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Optional
from repositories.database import get_db_connection


@dataclass
class ResponseRecordEntity:
    id: str
    attempt_id: str
    question_id: str
    prompt: str
    selected_option_id: str
    correct_option_id: str
    is_correct: bool
    explanation: Optional[str]


@dataclass
class AttemptEntity:
    id: str
    user_id: str
    quiz_id: str
    started_at: datetime
    expires_at: datetime
    completed_at: Optional[datetime] = None
    score: Optional[float] = None
    total_points: Optional[int] = None
    earned_points: Optional[int] = None
    passed: Optional[bool] = None


class AttemptRepository:
    def __init__(self) -> None:
        self._init_db()

    def _init_db(self) -> None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS attempts (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL REFERENCES users(id),
                        quiz_id TEXT NOT NULL REFERENCES quizzes(id),
                        started_at TIMESTAMPTZ NOT NULL,
                        expires_at TIMESTAMPTZ NOT NULL,
                        completed_at TIMESTAMPTZ,
                        score DOUBLE PRECISION,
                        total_points INTEGER,
                        earned_points INTEGER,
                        passed BOOLEAN
                    );

                    CREATE TABLE IF NOT EXISTS attempt_responses (
                        id TEXT PRIMARY KEY,
                        attempt_id TEXT NOT NULL REFERENCES attempts(id) ON DELETE CASCADE,
                        question_id TEXT NOT NULL,
                        prompt TEXT NOT NULL,
                        selected_option_id TEXT NOT NULL,
                        correct_option_id TEXT NOT NULL,
                        is_correct BOOLEAN NOT NULL,
                        explanation TEXT
                    );

                    CREATE INDEX IF NOT EXISTS idx_attempts_user ON attempts(user_id);
                    CREATE INDEX IF NOT EXISTS idx_attempts_quiz ON attempts(quiz_id);
                    CREATE INDEX IF NOT EXISTS idx_responses_attempt ON attempt_responses(attempt_id);
                    """
                )

    def create_attempt(self, attempt: AttemptEntity) -> AttemptEntity:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO attempts (id, user_id, quiz_id, started_at, expires_at)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        attempt.id,
                        attempt.user_id,
                        attempt.quiz_id,
                        attempt.started_at,
                        attempt.expires_at,
                    ),
                )
        return attempt

    def get_attempt_by_id(self, attempt_id: str) -> Optional[AttemptEntity]:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM attempts WHERE id = %s", (attempt_id,))
                row = cur.fetchone()
                if not row:
                    return None
                return self._row_to_attempt(row)

    def list_completed_attempts_by_user(self, user_id: str) -> List[AttemptEntity]:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM attempts 
                    WHERE user_id = %s AND completed_at IS NOT NULL 
                    ORDER BY completed_at DESC
                    """,
                    (user_id,),
                )
                rows = cur.fetchall()
                return [self._row_to_attempt(r) for r in rows]

    def list_completed_attempts_by_quiz(self, quiz_id: str) -> List[dict[str, Any]]:
        """Used by HistoryService for instructor analytics."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 
                        a.id,
                        a.user_id,
                        u.full_name AS user_name,
                        u.email AS user_email,
                        a.score,
                        a.total_points,
                        a.earned_points,
                        a.passed,
                        a.completed_at
                    FROM attempts a
                    JOIN users u ON a.user_id = u.id
                    WHERE a.quiz_id = %s AND a.completed_at IS NOT NULL
                    ORDER BY a.completed_at DESC
                    """,
                    (quiz_id,),
                )
                return cur.fetchall()

    def save_completion(
        self, attempt: AttemptEntity, responses: List[ResponseRecordEntity]
    ) -> None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE attempts
                    SET completed_at = %s, score = %s, total_points = %s, earned_points = %s, passed = %s
                    WHERE id = %s
                    """,
                    (
                        attempt.completed_at,
                        attempt.score,
                        attempt.total_points,
                        attempt.earned_points,
                        attempt.passed,
                        attempt.id,
                    ),
                )
                for resp in responses:
                    cur.execute(
                        """
                        INSERT INTO attempt_responses 
                        (id, attempt_id, question_id, prompt, selected_option_id, correct_option_id, is_correct, explanation)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            resp.id,
                            resp.attempt_id,
                            resp.question_id,
                            resp.prompt,
                            resp.selected_option_id,
                            resp.correct_option_id,
                            resp.is_correct,
                            resp.explanation,
                        ),
                    )

    def get_responses_for_attempt(self, attempt_id: str) -> List[ResponseRecordEntity]:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM attempt_responses WHERE attempt_id = %s",
                    (attempt_id,),
                )
                rows = cur.fetchall()
                return [
                    ResponseRecordEntity(
                        id=r["id"],
                        attempt_id=r["attempt_id"],
                        question_id=r["question_id"],
                        prompt=r["prompt"],
                        selected_option_id=r["selected_option_id"],
                        correct_option_id=r["correct_option_id"],
                        is_correct=r["is_correct"],
                        explanation=r["explanation"],
                    )
                    for r in rows
                ]

    @staticmethod
    def _row_to_attempt(row: dict[str, Any]) -> AttemptEntity:
        return AttemptEntity(
            id=row["id"],
            user_id=row["user_id"],
            quiz_id=row["quiz_id"],
            started_at=row["started_at"],
            expires_at=row["expires_at"],
            completed_at=row["completed_at"],
            score=row["score"],
            total_points=row["total_points"],
            earned_points=row["earned_points"],
            passed=row["passed"],
        )

    def list_completed_attempts_by_quiz(self, quiz_id: str) -> List[dict[str, Any]]:
        """Fetches all completed attempts for a target quiz with student names and emails."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 
                        a.id,
                        a.user_id,
                        u.full_name AS user_name,
                        u.email AS user_email,
                        a.score,
                        a.total_points,
                        a.earned_points,
                        a.passed,
                        a.completed_at
                    FROM attempts a
                    JOIN users u ON a.user_id = u.id
                    WHERE a.quiz_id = %s AND a.completed_at IS NOT NULL
                    ORDER BY a.completed_at DESC
                    """,
                    (quiz_id,),
                )
                return cur.fetchall()