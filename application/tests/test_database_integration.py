import os
import pytest
import uuid
from datetime import datetime, timezone, timedelta
import psycopg

from repositories.quiz_repo import QuizRepository, QuizEntity
from repositories.user_repo import UserRepository, UserEntity
from utils.security import hash_password

# This requires a live test PostgreSQL database to test raw psycopg SQL queries
# In a CI/CD pipeline, you would set TEST_DATABASE_URL
TEST_DB_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DB_URL,
    reason="TEST_DATABASE_URL environment variable is not set. Skipping DB integration tests."
)

@pytest.fixture
def override_db_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", TEST_DB_URL)

def test_user_repository_integration(override_db_url):
    repo = UserRepository()
    
    unique_email = f"test_{uuid.uuid4().hex[:6]}@example.com"
    user_id = str(uuid.uuid4())
    
    user = UserEntity(
        id=user_id,
        email=unique_email,
        full_name="Integration Test",
        role="student",
        hashed_password=hash_password("password"),
        created_at=datetime.now(timezone.utc)
    )
    
    # Test Create
    saved_user = repo.create(user)
    assert saved_user.id == user_id
    
    # Test Get by Email
    fetched_user = repo.get_by_email(unique_email)
    assert fetched_user is not None
    assert fetched_user.email == unique_email
    
    # Test Get by ID
    fetched_user_id = repo.get_by_id(user_id)
    assert fetched_user_id is not None
    assert fetched_user_id.full_name == "Integration Test"

def test_quiz_repository_integration(override_db_url):
    repo = QuizRepository()
    
    quiz_id = str(uuid.uuid4())
    
    quiz = QuizEntity(
        id=quiz_id,
        title="Integration Quiz",
        description="DB Test",
        subject="Integration",
        time_limit_minutes=15,
        passing_score_percentage=50,
        is_published=True,
        is_deleted=False,
        created_at=datetime.now(timezone.utc),
        questions=[]
    )
    
    # Test Create
    repo.create(quiz)
    
    # Test List Catalog
    catalog = repo.list_catalog(subject="Integration")
    assert len(catalog) >= 1
    
    # Test Soft Delete
    assert repo.soft_delete(quiz_id) is True
    
    # Verify it doesn't show up in catalog anymore
    catalog_after = repo.list_catalog(subject="Integration")
    assert not any(q.id == quiz_id for q, _ in catalog_after)
