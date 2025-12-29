from datetime import datetime, timedelta
from enum import Enum
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
    llm_config: Optional["ChallengeModelOut"] = None

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
    challengeTitle: Optional[str] = None
    challengeId: str
    currentPhase: int


class ChatResponse(BaseModel):
    content: str
    metadata: Optional[MessageMetadata] = None


class LLMProvider(str, Enum):
    openai = "openai"
    anthropic = "anthropic"
    gemini = "gemini"


class LLMMessage(BaseModel):
    role: str
    content: str


class LLMModelOut(BaseModel):
    id: str
    provider: LLMProvider
    description: Optional[str] = None


class LLMCompletionRequest(BaseModel):
    provider: LLMProvider
    model: str
    prompt: str
    max_tokens: Optional[int] = 256
    temperature: Optional[float] = 0.7


class LLMChatRequest(BaseModel):
    provider: LLMProvider
    model: str
    messages: List[LLMMessage]
    system_prompt: Optional[str] = None
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7


class ChallengeModelOut(BaseModel):
    challenge_id: str
    provider: LLMProvider
    model: str

    class Config:
        from_attributes = True


class ChallengeModelUpdate(BaseModel):
    provider: LLMProvider
    model: str


class ChallengeActivationUpdate(BaseModel):
    is_active: bool


class ChallengePromptUpdate(BaseModel):
    system_prompt: str


# Game Master Session Schemas

class SessionCreate(BaseModel):
    challenge_id: str


class SessionOut(BaseModel):
    id: str
    user_id: str
    challenge_id: str
    status: str
    current_step_index: int
    total_score: int
    max_possible_score: int
    mistakes_count: int
    hints_used: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AttemptSubmission(BaseModel):
    answer: int | str | List[int]  # MCQ index, text answer, or list of indices


class ActionSubmission(BaseModel):
    action: str  # "continue", "hint", etc.


class DisplayMessageOut(BaseModel):
    role: str
    content: str
    timestamp: str
    metadata: Optional[dict] = None


class SessionStateResponse(BaseModel):
    session: SessionOut
    ui_response: dict  # UI mode, step info, messages, etc.


ChallengeOut.model_rebuild()
