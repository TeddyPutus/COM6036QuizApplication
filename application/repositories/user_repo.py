from dataclasses import dataclass
from datetime import datetime
import sqlite3
from typing import Optional

DB_FILE = "quiz_app.db"


@dataclass
class UserEntity:
    id: str
    email: str
    full_name: str
    role: str
    hashed_password: str
    created_at: datetime


class UserRepository:
    def __init__(self, db_path: str = DB_FILE) -> None:
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    hashed_password TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def get_by_id(self, user_id: str) -> Optional[UserEntity]:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            return self._row_to_entity(row) if row else None

    def get_by_email(self, email: str) -> Optional[UserEntity]:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE lower(email) = lower(?)", (email,)
            ).fetchone()
            return self._row_to_entity(row) if row else None

    def create(self, user: UserEntity) -> UserEntity:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO users (id, email, full_name, role, hashed_password, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user.id,
                    user.email,
                    user.full_name,
                    user.role,
                    user.hashed_password,
                    user.created_at.isoformat(),
                ),
            )
        return user

    @staticmethod
    def _row_to_entity(row: sqlite3.Row) -> UserEntity:
        return UserEntity(
            id=row["id"],
            email=row["email"],
            full_name=row["full_name"],
            role=row["role"],
            hashed_password=row["hashed_password"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
