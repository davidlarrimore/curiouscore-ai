import uuid
from sqlalchemy import Column, String, DateTime, func, Boolean, Integer, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)
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
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    difficulty: Mapped[str] = mapped_column(String, default="beginner")
    system_prompt: Mapped[str] = mapped_column(Text)
    estimated_time_minutes: Mapped[int] = mapped_column(Integer, default=30)
    xp_reward: Mapped[int] = mapped_column(Integer, default=100)
    passing_score: Mapped[int] = mapped_column(Integer, default=70)
    help_resources: Mapped[list | None] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    progress = relationship("UserProgress", back_populates="challenge", cascade="all, delete-orphan")


class UserProgress(Base):
    __tablename__ = "user_progress"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"))
    challenge_id: Mapped[str] = mapped_column(String, ForeignKey("challenges.id", ondelete="CASCADE"))
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, default="not_started")
    messages: Mapped[list | None] = mapped_column(JSON, default=list)
    current_phase: Mapped[int] = mapped_column(Integer, default=1)
    mistakes_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="progress")
    challenge = relationship("Challenge", back_populates="progress")
