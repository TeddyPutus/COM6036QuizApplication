# database.py
import os
import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/quiz_app",
)


def get_db_connection():
    """Provides a PostgreSQL connection using dict_row for column-name access."""
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)