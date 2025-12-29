"""
Event Type Definitions

Events are the fundamental building blocks of the Game Master architecture.
All state changes flow through events, enabling deterministic replay.

Event Flow:
1. User action triggers API call
2. API creates event and appends to event store
3. Engine applies event to current state
4. Engine emits derived events
5. State is persisted via snapshot

Event Types:
- User-initiated: Actions from the user
- Engine-derived: Events emitted by engine logic
- LLM-task: Events related to LLM processing
"""

from enum import Enum
from typing import Any, Optional, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class EventType(str, Enum):
    """
    All possible event types in the system.
    Events are immutable once created.
    """
    # Session lifecycle
    SESSION_CREATED = "SESSION_CREATED"
    SESSION_STARTED = "SESSION_STARTED"
    SESSION_COMPLETED = "SESSION_COMPLETED"
    SESSION_ABANDONED = "SESSION_ABANDONED"

    # User actions
    USER_SUBMITTED_ANSWER = "USER_SUBMITTED_ANSWER"
    USER_REQUESTED_HINT = "USER_REQUESTED_HINT"
    USER_CONTINUED = "USER_CONTINUED"  # For CONTINUE_GATE

    # Engine-derived events
    STEP_ENTERED = "STEP_ENTERED"
    STEP_COMPLETED = "STEP_COMPLETED"
    STEP_FAILED = "STEP_FAILED"

    # Scoring events
    SCORE_AWARDED = "SCORE_AWARDED"
    SCORE_DEDUCTED = "SCORE_DEDUCTED"

    # LLM task events
    LLM_TASK_REQUESTED = "LLM_TASK_REQUESTED"
    LLM_TASK_COMPLETED = "LLM_TASK_COMPLETED"
    GM_NARRATED = "GM_NARRATED"
    LEM_EVALUATED = "LEM_EVALUATED"
    HINT_PROVIDED = "HINT_PROVIDED"


class Event(BaseModel):
    """
    Base event model.
    All events have these fields plus event-specific data.
    """
    model_config = ConfigDict(use_enum_values=True)

    event_type: EventType
    session_id: str
    sequence_number: int
    timestamp: datetime
    data: dict[str, Any]


# ============================================================================
# Event Data Schemas (Pydantic models for event.data field)
# ============================================================================


class SessionCreatedData(BaseModel):
    """Data for SESSION_CREATED event."""
    challenge_id: str
    user_id: str


class SessionStartedData(BaseModel):
    """Data for SESSION_STARTED event."""
    first_step_index: int = 0


class UserSubmittedAnswerData(BaseModel):
    """Data for USER_SUBMITTED_ANSWER event."""
    step_index: int
    answer: str | int | List[int]  # Type depends on step type


class UserRequestedHintData(BaseModel):
    """Data for USER_REQUESTED_HINT event."""
    step_index: int


class UserContinuedData(BaseModel):
    """Data for USER_CONTINUED event (CONTINUE_GATE)."""
    step_index: int
    action: str  # "continue", "review", etc.


class StepEnteredData(BaseModel):
    """Data for STEP_ENTERED event."""
    step_index: int
    step_type: str
    ui_mode: str


class StepCompletedData(BaseModel):
    """Data for STEP_COMPLETED event."""
    step_index: int
    score_awarded: int
    max_possible: int
    passed: bool


class StepFailedData(BaseModel):
    """Data for STEP_FAILED event."""
    step_index: int
    reason: str
    attempts: int


class SessionCompletedData(BaseModel):
    """Data for SESSION_COMPLETED event."""
    final_score: int
    max_possible_score: int
    completion_percentage: float
    passed: bool


class ScoreAwardedData(BaseModel):
    """Data for SCORE_AWARDED event."""
    step_index: int
    points: int
    reason: str


class LEMEvaluatedData(BaseModel):
    """Data for LEM_EVALUATED event."""
    step_index: int
    raw_score: int  # From LEM
    clamped_score: int  # After engine enforcement
    max_score: int
    passed: bool
    rationale: str
    tags: List[str]


class GMNarratedData(BaseModel):
    """Data for GM_NARRATED event."""
    step_index: int
    content: str
    task_type: str  # "introduction", "transition", "encouragement"


class HintProvidedData(BaseModel):
    """Data for HINT_PROVIDED event."""
    step_index: int
    hint_content: str
    hint_level: int  # Progressive hints


class LLMTaskRequestedData(BaseModel):
    """Data for LLM_TASK_REQUESTED event."""
    task_type: str  # GM_NARRATE, LEM_EVALUATE, TEACH_HINTS
    task_id: str
    step_index: int
    context: dict[str, Any]


class LLMTaskCompletedData(BaseModel):
    """Data for LLM_TASK_COMPLETED event."""
    task_type: str
    task_id: str
    step_index: int
    result: dict[str, Any]  # Type depends on task_type
