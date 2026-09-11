# repositories/attempt_repo.py
from dataclasses import dataclass
from datetime import datetime
import sqlite3
from typing import List, Optional

DB_FILE = "quiz_app.db"


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
    def __init__(self, db_path: str = DB_FILE) -> None:
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS attempts (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(id),
                    quiz_id TEXT NOT NULL REFERENCES quizzes(id),
                    started_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    completed_at TEXT,
                    score REAL,
                    total_points INTEGER,
                    earned_points INTEGER,
                    passed INTEGER
                );

                CREATE TABLE IF NOT EXISTS attempt_responses (
                    id TEXT PRIMARY KEY,
                    attempt_id TEXT NOT NULL REFERENCES attempts(id) ON DELETE CASCADE,
                    question_id TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    selected_option_id TEXT NOT NULL,
                    correct_option_id TEXT NOT NULL,
                    is_correct INTEGER NOT NULL,
                    explanation TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_attempts_user ON attempts(user_id);
                CREATE INDEX IF NOT EXISTS idx_attempts_quiz ON attempts(quiz_id);
                CREATE INDEX IF NOT EXISTS idx_responses_attempt ON attempt_responses(attempt_id);
                """
            )

    def create_attempt(self, attempt: AttemptEntity) -> AttemptEntity:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO attempts (id, user_id, quiz_id, started_at, expires_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    attempt.id,
                    attempt.user_id,
                    attempt.quiz_id,
                    attempt.started_at.isoformat(),
                    attempt.expires_at.isoformat(),
                ),
            )
        return attempt

    def get_attempt_by_id(self, attempt_id: str) -> Optional[AttemptEntity]:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM attempts WHERE id = ?", (attempt_id,)
            ).fetchone()
            if not row:
                return None
            return self._row_to_attempt(row)

    def list_completed_attempts_by_user(self, user_id: str) -> List[AttemptEntity]:
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM attempts 
                WHERE user_id = ? AND completed_at IS NOT NULL 
                ORDER BY completed_at DESC
                """,
                (user_id,),
            ).fetchall()
            return [self._row_to_attempt(r) for r in rows]

    def save_completion(
        self, attempt: AttemptEntity, responses: List[ResponseRecordEntity]
    ) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE attempts
                SET completed_at = ?, score = ?, total_points = ?, earned_points = ?, passed = ?
                WHERE id = ?
                """,
                (
                    attempt.completed_at.isoformat() if attempt.completed_at else None,
                    attempt.score,
                    attempt.total_points,
                    attempt.earned_points,
                    int(attempt.passed) if attempt.passed is not None else None,
                    attempt.id,
                ),
            )
            for resp in responses:
                conn.execute(
                    """
                    INSERT INTO attempt_responses 
                    (id, attempt_id, question_id, prompt, selected_option_id, correct_option_id, is_correct, explanation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        resp.id,
                        resp.attempt_id,
                        resp.question_id,
                        resp.prompt,
                        resp.selected_option_id,
                        resp.correct_option_id,
                        int(resp.is_correct),
                        resp.explanation,
                    ),
                )

    def get_responses_for_attempt(self, attempt_id: str) -> List[ResponseRecordEntity]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM attempt_responses WHERE attempt_id = ?", (attempt_id,)
            ).fetchall()
            return [
                ResponseRecordEntity(
                    id=r["id"],
                    attempt_id=r["attempt_id"],
                    question_id=r["question_id"],
                    prompt=r["prompt"],
                    selected_option_id=r["selected_option_id"],
                    correct_option_id=r["correct_option_id"],
                    is_correct=bool(r["is_correct"]),
                    explanation=r["explanation"],
                )
                for r in rows
            ]

    @staticmethod
    def _row_to_attempt(row: sqlite3.Row) -> AttemptEntity:
        return AttemptEntity(
            id=row["id"],
            user_id=row["user_id"],
            quiz_id=row["quiz_id"],
            started_at=datetime.fromisoformat(row["started_at"]),
            expires_at=datetime.fromisoformat(row["expires_at"]),
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            score=row["score"],
            total_points=row["total_points"],
            earned_points=row["earned_points"],
            passed=bool(row["passed"]) if row["passed"] is not None else None,
        )