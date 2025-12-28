from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserBase(BaseModel):
    id: str
    email: EmailStr
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str
    xp: int
    level: int
    created_at: datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    username: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ProfileUpdate(BaseModel):
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    xp: Optional[int] = None
    level: Optional[int] = None


class BadgeOut(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    badge_type: str
    xp_reward: int

    class Config:
        from_attributes = True


class UserBadgeOut(BaseModel):
    id: str
    badge_id: str
    earned_at: datetime
    badge: BadgeOut

    class Config:
        from_attributes = True


class ChallengeOut(BaseModel):
    id: str
    title: str
    description: str
    tags: List[str]
    difficulty: str
    system_prompt: str
    estimated_time_minutes: int
    xp_reward: int
    passing_score: int
    help_resources: list | None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class MessageMetadata(BaseModel):
    questionType: str
    options: Optional[List[str]] = None
    correctAnswer: Optional[int] = None
    phase: int
    progressIncrement: int
    scoreChange: int
    hint: Optional[str] = None
    isComplete: bool


class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime
    metadata: Optional[MessageMetadata] = None


class ProgressOut(BaseModel):
    id: str
    user_id: str
    challenge_id: str
    progress_percent: int
    score: int
    status: str
    messages: List[ChatMessage] | None
    current_phase: int
    mistakes_count: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProgressUpdate(BaseModel):
    progress_percent: Optional[int] = None
    score: Optional[int] = None
    status: Optional[str] = None
    messages: Optional[List[ChatMessage]] = None
    current_phase: Optional[int] = None
    mistakes_count: Optional[int] = None
    completed_at: Optional[datetime] = None


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    systemPrompt: str
    challengeTitle: str
    currentPhase: int


class ChatResponse(BaseModel):
    content: str
    metadata: Optional[MessageMetadata] = None
