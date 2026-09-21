from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    STUDENT = "student"
    INSTRUCTOR = "instructor"
    ADMIN = "admin"


# --- Authentication Schemas ---
class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    role: UserRole = UserRole.STUDENT


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: UserRole
    created_at: datetime


# --- Option & Question Schemas ---
class OptionBase(BaseModel):
    text: str


class OptionCreate(OptionBase):
    is_correct: bool


class StudentOptionResponse(OptionBase):
    id: str


class InstructorOptionResponse(OptionBase):
    id: str
    is_correct: bool


class QuestionCreate(BaseModel):
    prompt: str
    explanation: Optional[str] = None
    points: int = 1
    options: List[OptionCreate] = Field(..., min_length=2)


class StudentQuestionResponse(BaseModel):
    id: str
    prompt: str
    points: int
    options: List[StudentOptionResponse]


class InstructorQuestionResponse(BaseModel):
    id: str
    prompt: str
    points: int
    explanation: Optional[str]
    options: List[InstructorOptionResponse]


# --- Quiz Schemas ---
class QuizBase(BaseModel):
    title: str = Field(..., max_length=150)
    description: Optional[str] = None
    subject: str
    time_limit_minutes: int = Field(..., gt=0, le=180)
    passing_score_percentage: float = Field(default=70.0, ge=0.0, le=100.0)


class QuizCreateRequest(QuizBase):
    questions: List[QuestionCreate] = Field(..., min_length=1)


class QuizSummaryResponse(QuizBase):
    id: str
    total_questions: int
    is_published: bool
    created_at: datetime


class QuizTakeResponse(BaseModel):
    """Payload delivered to student client. Strips all grading logic and correct answers."""
    quiz_id: str
    title: str
    time_limit_minutes: int
    questions: List[StudentQuestionResponse]


# --- Attempt & Grading Schemas ---
class AttemptStartRequest(BaseModel):
    quiz_id: str


class AttemptStartResponse(BaseModel):
    attempt_id: str
    quiz_id: str
    started_at: datetime
    expires_at: datetime


class AnswerSubmission(BaseModel):
    question_id: str
    selected_option_id: str


class AttemptSubmitRequest(BaseModel):
    answers: List[AnswerSubmission]


class QuestionResultFeedback(BaseModel):
    question_id: str
    prompt: str
    selected_option_id: str
    selected_option_text: Optional[str] = None
    correct_option_id: str
    correct_option_text: Optional[str] = None
    is_correct: bool
    explanation: Optional[str]


class AttemptResultResponse(BaseModel):
    attempt_id: str
    quiz_id: str
    score: float
    total_points: int
    earned_points: int
    passed: bool
    completed_at: datetime
    breakdown: Optional[List[QuestionResultFeedback]] = None

class InstructorAttemptResponse(BaseModel):
    attempt_id: str
    user_id: str
    user_name: str
    user_email: str
    score: float
    total_points: int
    earned_points: int
    passed: bool
    completed_at: datetime

class QuizAnalyticsSummary(BaseModel):
    quiz_id: str
    quiz_title: str
    total_attempts: int
    passed_attempts: int
    pass_rate_percentage: float
    average_score: float
    highest_score: float
    lowest_score: float