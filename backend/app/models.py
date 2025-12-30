from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import Column, String, DateTime, func, Boolean, Integer, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    username: Mapped[str] = mapped_column(String, nullable=True)
    avatar_url: Mapped[str] = mapped_column(String, nullable=True)
    role: Mapped[str] = mapped_column(String, default="user")
    xp: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    badges = relationship("UserBadge", back_populates="user", cascade="all, delete-orphan")
    progress = relationship("UserProgress", back_populates="user", cascade="all, delete-orphan")


class Badge(Base):
    __tablename__ = "badges"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    icon: Mapped[str] = mapped_column(String)
    badge_type: Mapped[str] = mapped_column(String)
    xp_reward: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user_badges = relationship("UserBadge", back_populates="badge", cascade="all, delete-orphan")


class UserBadge(Base):
    __tablename__ = "user_badges"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"))
    badge_id: Mapped[str] = mapped_column(String, ForeignKey("badges.id", ondelete="CASCADE"))
    earned_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="badges")
    badge = relationship("Badge", back_populates="user_badges")


class Challenge(Base):
    __tablename__ = "challenges"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    difficulty: Mapped[str] = mapped_column(String, default="beginner")
    system_prompt: Mapped[str] = mapped_column(Text)
    estimated_time_minutes: Mapped[int] = mapped_column(Integer, default=30)
    xp_reward: Mapped[int] = mapped_column(Integer, default=100)
    passing_score: Mapped[int] = mapped_column(Integer, default=70)
    help_resources: Mapped[list] = mapped_column(JSON, nullable=True, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Challenge type: "simple" (prompt-driven) or "advanced" (step-based)
    challenge_type: Mapped[str] = mapped_column(String, default="simple")

    # Custom variables for prompt substitution (e.g., {"course_name": "Python 101"})
    custom_variables: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)

    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Legacy relationships
    progress = relationship("UserProgress", back_populates="challenge", cascade="all, delete-orphan")
    llm_config = relationship(
        "ChallengeModel",
        back_populates="challenge",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin",
    )

    # Game Master architecture relationships
    steps = relationship("ChallengeStep", back_populates="challenge", cascade="all, delete-orphan", order_by="ChallengeStep.step_index")
    personas = relationship("Persona", back_populates="challenge", cascade="all, delete-orphan")
    scenes = relationship("Scene", back_populates="challenge", cascade="all, delete-orphan", order_by="Scene.scene_index")
    media_assets = relationship("MediaAsset", back_populates="challenge", cascade="all, delete-orphan")
    knowledge_base = relationship("KnowledgeBase", back_populates="challenge", cascade="all, delete-orphan")


class UserProgress(Base):
    __tablename__ = "user_progress"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"))
    challenge_id: Mapped[str] = mapped_column(String, ForeignKey("challenges.id", ondelete="CASCADE"))
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, default="not_started")
    messages: Mapped[list] = mapped_column(JSON, nullable=True, default=list)
    current_phase: Mapped[int] = mapped_column(Integer, default=1)
    mistakes_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="progress")
    challenge = relationship("Challenge", back_populates="progress")


class ChallengeModel(Base):
    __tablename__ = "challenge_models"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    challenge_id: Mapped[str] = mapped_column(String, ForeignKey("challenges.id", ondelete="CASCADE"), unique=True)
    provider: Mapped[str] = mapped_column(String)
    model: Mapped[str] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    challenge = relationship("Challenge", back_populates="llm_config", lazy="selectin")


# ============================================================================
# Game Master Architecture Models
# ============================================================================


class GameSession(Base):
    """
    Game session tracks user progress through a challenge using event sourcing.
    Replaces UserProgress for the new Game Master architecture.
    """
    __tablename__ = "game_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    challenge_id: Mapped[str] = mapped_column(String, ForeignKey("challenges.id", ondelete="CASCADE"), index=True)

    # Session state
    status: Mapped[str] = mapped_column(String, default="created")  # created, active, completed, abandoned
    current_step_index: Mapped[int] = mapped_column(Integer, default=0)

    # Aggregate scores (engine owns these, never LLM)
    total_score: Mapped[int] = mapped_column(Integer, default=0)
    max_possible_score: Mapped[int] = mapped_column(Integer, default=100)

    # Tracking metrics
    mistakes_count: Mapped[int] = mapped_column(Integer, default=0)
    hints_used: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User")
    challenge = relationship("Challenge")
    events = relationship("GameEvent", back_populates="session", cascade="all, delete-orphan", order_by="GameEvent.sequence_number")
    snapshots = relationship("SessionSnapshot", back_populates="session", cascade="all, delete-orphan")


class GameEvent(Base):
    """
    Append-only event log for deterministic replay.
    All state changes flow through events.
    """
    __tablename__ = "game_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String, ForeignKey("game_sessions.id", ondelete="CASCADE"), index=True)

    # Event identification
    event_type: Mapped[str] = mapped_column(String, index=True)  # SESSION_CREATED, USER_SUBMITTED_ANSWER, etc.
    event_data: Mapped[dict] = mapped_column(JSON)  # Event-specific payload
    sequence_number: Mapped[int] = mapped_column(Integer)  # For deterministic replay

    # Metadata
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    session = relationship("GameSession", back_populates="events")


class ChallengeStep(Base):
    """
    Individual step within a challenge.
    Challenges are composed of multiple steps, each with specific UI mode and scoring.
    """
    __tablename__ = "challenge_steps"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    challenge_id: Mapped[str] = mapped_column(String, ForeignKey("challenges.id", ondelete="CASCADE"), index=True)
    step_index: Mapped[int] = mapped_column(Integer)  # Ordering within challenge

    # Step configuration
    step_type: Mapped[str] = mapped_column(String)  # CHAT, MCQ_SINGLE, MCQ_MULTI, TRUE_FALSE, FILE_UPLOAD, CONTINUE_GATE
    title: Mapped[str] = mapped_column(String)
    instruction: Mapped[str] = mapped_column(Text)  # What the user needs to do

    # MCQ-specific fields
    options: Mapped[list] = mapped_column(JSON, nullable=True)  # For MCQ types
    correct_answer: Mapped[int] = mapped_column(Integer, nullable=True)  # For MCQ_SINGLE/TRUE_FALSE (index)
    correct_answers: Mapped[list] = mapped_column(JSON, nullable=True)  # For MCQ_MULTI (list of indices)

    # Scoring configuration (engine owns this, not LLM)
    points_possible: Mapped[int] = mapped_column(Integer, default=10)
    passing_threshold: Mapped[float] = mapped_column(Integer, default=70)  # 70% as integer (0-100)

    # LEM rubric (for CHAT type free-text evaluation)
    rubric: Mapped[dict] = mapped_column(JSON, nullable=True)
    # Rubric structure:
    # {
    #   "criteria": [{"name": "completeness", "weight": 0.4, "description": "..."}],
    #   "examples": {"excellent": "...", "good": "...", "poor": "..."}
    # }

    # Narrative configuration
    gm_context: Mapped[str] = mapped_column(Text, nullable=True)  # Context for GM narration
    auto_narrate: Mapped[bool] = mapped_column(Boolean, default=True)  # Should GM narrate on step entry?

    # Timestamps
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    challenge = relationship("Challenge", back_populates="steps")


class SessionSnapshot(Base):
    """
    Point-in-time state snapshot for fast hydration.
    Snapshots are created periodically (e.g., every 5 events) to avoid replaying entire event log.
    """
    __tablename__ = "session_snapshots"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String, ForeignKey("game_sessions.id", ondelete="CASCADE"), index=True)

    # Complete state at this point (SessionState as JSON)
    snapshot_data: Mapped[dict] = mapped_column(JSON)
    # Structure:
    # {
    #   "current_step_index": 2,
    #   "step_scores": [{"step_index": 0, "score": 8, "max": 10}, ...],
    #   "messages": [...],
    #   "current_ui_mode": "CHAT",
    #   "context_summary": "User has completed intro...",
    #   "flags": {"showed_hint_on_step_1": true}
    # }

    event_sequence: Mapped[int] = mapped_column(Integer)  # Which event this snapshot is valid up to
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    session = relationship("GameSession", back_populates="snapshots")


# ============================================================================
# Game Master Content Models (Personas, Scenes, Media, Knowledge Base)
# ============================================================================


class Persona(Base):
    """
    Character/persona that can interact with learners.
    Can be global (reusable across challenges) or challenge-specific.
    """
    __tablename__ = "personas"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    challenge_id: Mapped[str] = mapped_column(String, ForeignKey("challenges.id", ondelete="CASCADE"), nullable=True, index=True)

    # Identity
    name: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)  # e.g., "Senior Developer", "Product Manager"
    temperament: Mapped[str] = mapped_column(String)  # e.g., "friendly and patient", "direct and technical"

    # Behavioral constraints
    communication_style: Mapped[str] = mapped_column(Text)  # Tone constraints
    knowledge_scope: Mapped[str] = mapped_column(Text)  # What they know/don't know
    facts: Mapped[dict] = mapped_column(JSON, default=dict)  # Grounded profile fields

    # Presentation
    avatar_url: Mapped[str] = mapped_column(String, nullable=True)

    # Timestamps
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    challenge = relationship("Challenge", back_populates="personas")


class Scene(Base):
    """
    Scene configuration for narrative delivery.
    Defines background media, audio, theme, and active speakers for a challenge.
    """
    __tablename__ = "scenes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    challenge_id: Mapped[str] = mapped_column(String, ForeignKey("challenges.id", ondelete="CASCADE"), index=True)
    scene_index: Mapped[int] = mapped_column(Integer)  # Order within challenge

    # Scene configuration
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)

    # Media
    background_media_url: Mapped[str] = mapped_column(String, nullable=True)  # Image/video background
    ambient_audio_url: Mapped[str] = mapped_column(String, nullable=True)

    # UI theming
    theme_accents: Mapped[dict] = mapped_column(JSON, nullable=True)  # UI theme overrides

    # Active speakers
    active_speakers: Mapped[list] = mapped_column(JSON, default=list)  # ["GM", "PERSONA:<id>", ...]

    # Timestamp
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    challenge = relationship("Challenge", back_populates="scenes")


class MediaAsset(Base):
    """
    Media files (images, videos, audio, documents).
    Can be global (reusable) or challenge-specific.
    """
    __tablename__ = "media_assets"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    challenge_id: Mapped[str] = mapped_column(String, ForeignKey("challenges.id", ondelete="CASCADE"), nullable=True, index=True)
    uploaded_by: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), index=True)

    # Asset metadata
    asset_type: Mapped[str] = mapped_column(String)  # "image", "video", "audio", "document"
    filename: Mapped[str] = mapped_column(String)
    file_url: Mapped[str] = mapped_column(String)  # S3/CDN URL or local path
    file_size: Mapped[int] = mapped_column(Integer)  # bytes
    mime_type: Mapped[str] = mapped_column(String)

    # Timestamp
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    challenge = relationship("Challenge", back_populates="media_assets")
    user = relationship("User")


class KnowledgeBase(Base):
    """
    Teaching materials and references.
    Can be global (reusable) or challenge-specific.
    """
    __tablename__ = "knowledge_base"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    challenge_id: Mapped[str] = mapped_column(String, ForeignKey("challenges.id", ondelete="CASCADE"), nullable=True, index=True)

    # Content
    title: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)  # Markdown content
    content_type: Mapped[str] = mapped_column(String)  # "text", "code_example", "diagram", "external_link"
    tags: Mapped[list] = mapped_column(JSON, default=list)
    external_url: Mapped[str] = mapped_column(String, nullable=True)

    # Future: Vector search
    embedding_vector: Mapped[str] = mapped_column(String, nullable=True)

    # Timestamps
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    challenge = relationship("Challenge", back_populates="knowledge_base")
