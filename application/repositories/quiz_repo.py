# repositories/quiz_repo.py
from dataclasses import dataclass, field
from datetime import datetime
import sqlite3
from typing import List, Optional

DB_FILE = "quiz_app.db"


@dataclass
class OptionEntity:
    id: str
    question_id: str
    text: str
    is_correct: bool


@dataclass
class QuestionEntity:
    id: str
    quiz_id: str
    prompt: str
    points: int
    explanation: Optional[str] = None
    options: List[OptionEntity] = field(default_factory=list)


@dataclass
class QuizEntity:
    id: str
    title: str
    description: Optional[str]
    subject: str
    time_limit_minutes: int
    passing_score_percentage: float
    is_published: bool
    is_deleted: bool
    created_at: datetime
    questions: List[QuestionEntity] = field(default_factory=list)


class QuizRepository:
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
                CREATE TABLE IF NOT EXISTS quizzes (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    subject TEXT NOT NULL,
                    time_limit_minutes INTEGER NOT NULL,
                    passing_score_percentage REAL NOT NULL,
                    is_published INTEGER NOT NULL DEFAULT 1,
                    is_deleted INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS questions (
                    id TEXT PRIMARY KEY,
                    quiz_id TEXT NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
                    prompt TEXT NOT NULL,
                    points INTEGER NOT NULL DEFAULT 1,
                    explanation TEXT
                );

                CREATE TABLE IF NOT EXISTS options (
                    id TEXT PRIMARY KEY,
                    question_id TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
                    text TEXT NOT NULL,
                    is_correct INTEGER NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_quizzes_subject ON quizzes(subject);
                CREATE INDEX IF NOT EXISTS idx_questions_quiz ON questions(quiz_id);
                CREATE INDEX IF NOT EXISTS idx_options_question ON options(question_id);
                """
            )

    def list_catalog(
        self, subject: Optional[str] = None, limit: int = 20, offset: int = 0
    ) -> List[tuple[QuizEntity, int]]:
        """Returns active quizzes with question counts."""
        query = """
            SELECT q.*, COUNT(qu.id) as question_count
            FROM quizzes q
            LEFT JOIN questions qu ON q.id = qu.quiz_id
            WHERE q.is_deleted = 0 AND q.is_published = 1
        """
        params: list = []

        if subject:
            query += " AND LOWER(q.subject) = LOWER(?)"
            params.append(subject)

        query += " GROUP BY q.id ORDER BY q.created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            results = []
            for r in rows:
                entity = QuizEntity(
                    id=r["id"],
                    title=r["title"],
                    description=r["description"],
                    subject=r["subject"],
                    time_limit_minutes=r["time_limit_minutes"],
                    passing_score_percentage=r["passing_score_percentage"],
                    is_published=bool(r["is_published"]),
                    is_deleted=bool(r["is_deleted"]),
                    created_at=datetime.fromisoformat(r["created_at"]),
                )
                results.append((entity, r["question_count"]))
            return results

    def get_by_id(self, quiz_id: str) -> Optional[QuizEntity]:
        """Fetches full quiz entity tree with nested questions and options."""
        with self._get_connection() as conn:
            quiz_row = conn.execute(
                "SELECT * FROM quizzes WHERE id = ? AND is_deleted = 0", (quiz_id,)
            ).fetchone()
            if not quiz_row:
                return None

            q_rows = conn.execute(
                "SELECT * FROM questions WHERE quiz_id = ?", (quiz_id,)
            ).fetchall()

            questions: List[QuestionEntity] = []
            for qr in q_rows:
                opt_rows = conn.execute(
                    "SELECT * FROM options WHERE question_id = ?", (qr["id"],)
                ).fetchall()
                options = [
                    OptionEntity(
                        id=opr["id"],
                        question_id=opr["question_id"],
                        text=opr["text"],
                        is_correct=bool(opr["is_correct"]),
                    )
                    for opr in opt_rows
                ]
                questions.append(
                    QuestionEntity(
                        id=qr["id"],
                        quiz_id=qr["quiz_id"],
                        prompt=qr["prompt"],
                        points=qr["points"],
                        explanation=qr["explanation"],
                        options=options,
                    )
                )

            return QuizEntity(
                id=quiz_row["id"],
                title=quiz_row["title"],
                description=quiz_row["description"],
                subject=quiz_row["subject"],
                time_limit_minutes=quiz_row["time_limit_minutes"],
                passing_score_percentage=quiz_row["passing_score_percentage"],
                is_published=bool(quiz_row["is_published"]),
                is_deleted=bool(quiz_row["is_deleted"]),
                created_at=datetime.fromisoformat(quiz_row["created_at"]),
                questions=questions,
            )

    def create(self, quiz: QuizEntity) -> QuizEntity:
        """Atomic insert of quiz, questions, and options."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO quizzes (id, title, description, subject, time_limit_minutes, passing_score_percentage, is_published, is_deleted, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    quiz.id,
                    quiz.title,
                    quiz.description,
                    quiz.subject,
                    quiz.time_limit_minutes,
                    quiz.passing_score_percentage,
                    int(quiz.is_published),
                    int(quiz.is_deleted),
                    quiz.created_at.isoformat(),
                ),
            )
            for q in quiz.questions:
                conn.execute(
                    "INSERT INTO questions (id, quiz_id, prompt, points, explanation) VALUES (?, ?, ?, ?, ?)",
                    (q.id, quiz.id, q.prompt, q.points, q.explanation),
                )
                for opt in q.options:
                    conn.execute(
                        "INSERT INTO options (id, question_id, text, is_correct) VALUES (?, ?, ?, ?)",
                        (opt.id, q.id, opt.text, int(opt.is_correct)),
                    )
        return quiz

    def soft_delete(self, quiz_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE quizzes SET is_deleted = 1 WHERE id = ? AND is_deleted = 0",
                (quiz_id,),
            )
            return cursor.rowcount > 0