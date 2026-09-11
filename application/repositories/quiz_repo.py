# repositories/quiz_repo.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from repositories.database import get_db_connection


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
    def __init__(self) -> None:
        self._init_db()

    def _init_db(self) -> None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS quizzes (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT,
                        subject TEXT NOT NULL,
                        time_limit_minutes INTEGER NOT NULL,
                        passing_score_percentage DOUBLE PRECISION NOT NULL,
                        is_published BOOLEAN NOT NULL DEFAULT TRUE,
                        is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
                        created_at TIMESTAMPTZ NOT NULL
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
                        is_correct BOOLEAN NOT NULL
                    );

                    CREATE INDEX IF NOT EXISTS idx_quizzes_subject ON quizzes(subject);
                    CREATE INDEX IF NOT EXISTS idx_questions_quiz ON questions(quiz_id);
                    CREATE INDEX IF NOT EXISTS idx_options_question ON options(question_id);
                    """
                )

    def list_catalog(
        self, subject: Optional[str] = None, limit: int = 20, offset: int = 0
    ) -> List[tuple[QuizEntity, int]]:
        query = """
            SELECT q.*, COUNT(qu.id) as question_count
            FROM quizzes q
            LEFT JOIN questions qu ON q.id = qu.quiz_id
            WHERE q.is_deleted = FALSE AND q.is_published = TRUE
        """
        params: list = []

        if subject:
            query += " AND LOWER(q.subject) = LOWER(%s)"
            params.append(subject)

        query += " GROUP BY q.id ORDER BY q.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
                results = []
                for r in rows:
                    entity = QuizEntity(
                        id=r["id"],
                        title=r["title"],
                        description=r["description"],
                        subject=r["subject"],
                        time_limit_minutes=r["time_limit_minutes"],
                        passing_score_percentage=r["passing_score_percentage"],
                        is_published=r["is_published"],
                        is_deleted=r["is_deleted"],
                        created_at=r["created_at"],
                    )
                    results.append((entity, r["question_count"]))
                return results

    def get_by_id(self, quiz_id: str) -> Optional[QuizEntity]:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM quizzes WHERE id = %s AND is_deleted = FALSE",
                    (quiz_id,),
                )
                quiz_row = cur.fetchone()
                if not quiz_row:
                    return None

                cur.execute("SELECT * FROM questions WHERE quiz_id = %s", (quiz_id,))
                q_rows = cur.fetchall()

                questions: List[QuestionEntity] = []
                for qr in q_rows:
                    cur.execute("SELECT * FROM options WHERE question_id = %s", (qr["id"],))
                    opt_rows = cur.fetchall()
                    options = [
                        OptionEntity(
                            id=opr["id"],
                            question_id=opr["question_id"],
                            text=opr["text"],
                            is_correct=opr["is_correct"],
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
                    is_published=quiz_row["is_published"],
                    is_deleted=quiz_row["is_deleted"],
                    created_at=quiz_row["created_at"],
                    questions=questions,
                )

    def create(self, quiz: QuizEntity) -> QuizEntity:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO quizzes (id, title, description, subject, time_limit_minutes, passing_score_percentage, is_published, is_deleted, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        quiz.id,
                        quiz.title,
                        quiz.description,
                        quiz.subject,
                        quiz.time_limit_minutes,
                        quiz.passing_score_percentage,
                        quiz.is_published,
                        quiz.is_deleted,
                        quiz.created_at,
                    ),
                )
                for q in quiz.questions:
                    cur.execute(
                        "INSERT INTO questions (id, quiz_id, prompt, points, explanation) VALUES (%s, %s, %s, %s, %s)",
                        (q.id, quiz.id, q.prompt, q.points, q.explanation),
                    )
                    for opt in q.options:
                        cur.execute(
                            "INSERT INTO options (id, question_id, text, is_correct) VALUES (%s, %s, %s, %s)",
                            (opt.id, q.id, opt.text, opt.is_correct),
                        )
        return quiz

    def soft_delete(self, quiz_id: str) -> bool:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE quizzes SET is_deleted = TRUE WHERE id = %s AND is_deleted = FALSE",
                    (quiz_id,),
                )
                return cur.rowcount > 0