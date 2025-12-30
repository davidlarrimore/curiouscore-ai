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
    challenge_type: str = "simple"
    custom_variables: Optional[dict] = None
    created_at: datetime
    llm_config: Optional["ChallengeModelOut"] = None

    class Config:
        from_attributes = True


class MessageMetadata(BaseModel):
    questionType: Optional[str] = None
    options: Optional[List[str]] = None
    correctAnswer: Optional[int] = None
    phase: Optional[int] = None
    progressIncrement: Optional[int] = None
    scoreChange: Optional[int] = None
    hint: Optional[str] = None
    isComplete: Optional[bool] = None


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


# ============================================================================
# Game Master Content Schemas (Personas, Scenes, Media, Knowledge Base, Steps)
# ============================================================================

# Persona schemas
class PersonaBase(BaseModel):
    name: str
    role: str
    temperament: str
    communication_style: str
    knowledge_scope: str
    facts: dict = {}
    avatar_url: Optional[str] = None
    challenge_id: Optional[str] = None  # NULL = global


class PersonaCreate(PersonaBase):
    pass


class PersonaUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    temperament: Optional[str] = None
    communication_style: Optional[str] = None
    knowledge_scope: Optional[str] = None
    facts: Optional[dict] = None
    avatar_url: Optional[str] = None
    challenge_id: Optional[str] = None


class PersonaOut(PersonaBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Scene schemas
class SceneBase(BaseModel):
    title: str
    description: str
    scene_index: int
    background_media_url: Optional[str] = None
    ambient_audio_url: Optional[str] = None
    theme_accents: Optional[dict] = None
    active_speakers: List[str] = []


class SceneCreate(SceneBase):
    challenge_id: str


class SceneUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    scene_index: Optional[int] = None
    background_media_url: Optional[str] = None
    ambient_audio_url: Optional[str] = None
    theme_accents: Optional[dict] = None
    active_speakers: Optional[List[str]] = None


class SceneOut(SceneBase):
    id: str
    challenge_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# MediaAsset schemas
class MediaAssetCreate(BaseModel):
    filename: str
    mime_type: str
    asset_type: str  # "image", "video", "audio", "document"
    challenge_id: Optional[str] = None


class MediaAssetPresignResponse(BaseModel):
    asset_id: str
    upload_url: str  # For direct upload
    file_url: str  # Final URL for access


class MediaAssetOut(BaseModel):
    id: str
    asset_type: str
    filename: str
    file_url: str
    file_size: int
    mime_type: str
    challenge_id: Optional[str]
    uploaded_by: str
    created_at: datetime

    class Config:
        from_attributes = True


# KnowledgeBase schemas
class KnowledgeBaseBase(BaseModel):
    title: str
    content: str
    content_type: str  # "text", "code_example", "diagram", "external_link"
    tags: List[str] = []
    external_url: Optional[str] = None
    challenge_id: Optional[str] = None


class KnowledgeBaseCreate(KnowledgeBaseBase):
    pass


class KnowledgeBaseUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    content_type: Optional[str] = None
    tags: Optional[List[str]] = None
    external_url: Optional[str] = None
    challenge_id: Optional[str] = None


class KnowledgeBaseOut(KnowledgeBaseBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ChallengeStep schemas
class ChallengeStepBase(BaseModel):
    step_index: int
    step_type: str  # "CHAT", "MCQ_SINGLE", "MCQ_MULTI", "TRUE_FALSE", "FILE_UPLOAD", "CONTINUE_GATE"
    title: str
    instruction: str
    options: Optional[List[str]] = None
    correct_answer: Optional[int] = None
    correct_answers: Optional[List[int]] = None
    points_possible: int = 10
    passing_threshold: int = 70  # Integer 0-100
    rubric: Optional[dict] = None
    gm_context: Optional[str] = None
    auto_narrate: bool = True


class ChallengeStepCreate(ChallengeStepBase):
    challenge_id: str


class ChallengeStepUpdate(BaseModel):
    step_index: Optional[int] = None
    step_type: Optional[str] = None
    title: Optional[str] = None
    instruction: Optional[str] = None
    options: Optional[List[str]] = None
    correct_answer: Optional[int] = None
    correct_answers: Optional[List[int]] = None
    points_possible: Optional[int] = None
    passing_threshold: Optional[int] = None
    rubric: Optional[dict] = None
    gm_context: Optional[str] = None
    auto_narrate: Optional[bool] = None


class ChallengeStepOut(ChallengeStepBase):
    id: str
    challenge_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# Enhanced Challenge schemas with relationships
class ChallengeCreate(BaseModel):
    title: str
    description: str
    tags: List[str] = []
    difficulty: str = "beginner"
    system_prompt: str
    estimated_time_minutes: int = 30
    xp_reward: int = 100
    passing_score: int = 70
    help_resources: List = []
    is_active: bool = True
    challenge_type: str = "simple"
    custom_variables: Optional[dict] = None


class ChallengeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    difficulty: Optional[str] = None
    system_prompt: Optional[str] = None
    estimated_time_minutes: Optional[int] = None
    xp_reward: Optional[int] = None
    passing_score: Optional[int] = None
    help_resources: Optional[List] = None
    is_active: Optional[bool] = None
    challenge_type: Optional[str] = None
    custom_variables: Optional[dict] = None


class ChallengeOutDetailed(ChallengeOut):
    """Enhanced challenge output with all relationships loaded."""
    steps: List[ChallengeStepOut] = []
    personas: List[PersonaOut] = []
    scenes: List[SceneOut] = []
    knowledge_base: List[KnowledgeBaseOut] = []

    class Config:
        from_attributes = True


# Pagination response
class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    pages: int
    limit: int


# Step reorder request
class StepReorderRequest(BaseModel):
    step_ids: List[str]  # Ordered list of step IDs


ChallengeOut.model_rebuild()
