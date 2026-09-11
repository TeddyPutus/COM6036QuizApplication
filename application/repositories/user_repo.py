# repositories/user_repo.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from repositories.database import get_db_connection


@dataclass
class UserEntity:
    id: str
    email: str
    full_name: str
    role: str
    hashed_password: str
    created_at: datetime


class UserRepository:
    def __init__(self) -> None:
        self._init_db()

    def _init_db(self) -> None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        full_name TEXT NOT NULL,
                        role TEXT NOT NULL,
                        hashed_password TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL
                    );
                    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
                    """
                )

    def get_by_email(self, email: str) -> Optional[UserEntity]:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM users WHERE LOWER(email) = LOWER(%s)",
                    (email,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                return UserEntity(
                    id=row["id"],
                    email=row["email"],
                    full_name=row["full_name"],
                    role=row["role"],
                    hashed_password=row["hashed_password"],
                    created_at=row["created_at"],
                )

    def get_by_id(self, user_id: str) -> Optional[UserEntity]:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                row = cur.fetchone()
                if not row:
                    return None
                return UserEntity(
                    id=row["id"],
                    email=row["email"],
                    full_name=row["full_name"],
                    role=row["role"],
                    hashed_password=row["hashed_password"],
                    created_at=row["created_at"],
                )

    def create(self, user: UserEntity) -> UserEntity:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (id, email, full_name, role, hashed_password, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        user.id,
                        user.email,
                        user.full_name,
                        user.role,
                        user.hashed_password,
                        user.created_at,
                    ),
                )
        return user