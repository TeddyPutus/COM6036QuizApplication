from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional


@dataclass
class UserEntity:
    id: str
    email: str
    full_name: str
    role: str
    hashed_password: str
    created_at: datetime


class UserRepository:
    """In-memory DAL implementation. Can be replaced with SQLAlchemy without touching service logic."""
    def __init__(self) -> None:
        self._users_by_id: Dict[str, UserEntity] = {}
        self._users_by_email: Dict[str, UserEntity] = {}

    def get_by_id(self, user_id: str) -> Optional[UserEntity]:
        return self._users_by_id.get(user_id)

    def get_by_email(self, email: str) -> Optional[UserEntity]:
        return self._users_by_email.get(email.lower())

    def create(self, user: UserEntity) -> UserEntity:
        self._users_by_id[user.id] = user
        self._users_by_email[user.email.lower()] = user
        return user


user_repository = UserRepository()