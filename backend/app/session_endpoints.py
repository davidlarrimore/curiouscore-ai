"""
Session API Endpoints

Handles game session lifecycle with event-driven architecture:
- POST /sessions - Create new session
- POST /sessions/{id}/start - Start session (enter first step)
- POST /sessions/{id}/attempt - Submit answer for scoring
- POST /sessions/{id}/action - Perform non-graded action
- GET /sessions/{id}/state - Get current session state
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from .database import get_session
from .deps import get_current_user
from .models import GameSession, ChallengeStep, User
from .schemas import (
    SessionCreate,
    SessionOut,
    SessionStateResponse,
    AttemptSubmission,
    ActionSubmission,
)
from .game_engine.engine import GameEngine
from .game_engine.events import Event, EventType
from .game_engine.state import SessionState
from .game_engine.step_handlers import get_handler_for_step_type
from .event_store import (
    append_event,
    hydrate_state,
    append_and_snapshot,
)


router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Create a new game session.
    Status: 'created' (not started yet).
    """
    # Create session record
    session = GameSession(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        challenge_id=payload.challenge_id,
        status="created"
    )

    db.add(session)

    # Create SESSION_CREATED event
    await append_event(
        db=db,
        session_id=session.id,
        event_type=EventType.SESSION_CREATED,
        event_data={
            "challenge_id": payload.challenge_id,
            "user_id": current_user.id
        },
        sequence_number=0
    )

    await db.commit()
    await db.refresh(session)

    return session


@router.post("/{session_id}/start", response_model=SessionStateResponse)
async def start_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Start a game session (enter first step).
    Applies SESSION_STARTED event and enters first step.
    """
    # Load session
    result = await db.execute(
        select(GameSession).where(GameSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if session.status != "created":
        raise HTTPException(status_code=400, detail="Session already started")

    # Load challenge steps
    result = await db.execute(
        select(ChallengeStep)
        .where(ChallengeStep.challenge_id == session.challenge_id)
        .order_by(ChallengeStep.step_index)
    )
    steps = list(result.scalars().all())

    if not steps:
        raise HTTPException(status_code=400, detail="Challenge has no steps")

    # Create engine
    engine = GameEngine(steps)

    # Hydrate current state
    state, latest_seq = await hydrate_state(
        db=db,
        session_id=session_id,
        challenge_id=session.challenge_id,
        user_id=current_user.id,
        engine=engine
    )

    # Create SESSION_STARTED event
    event = Event(
        event_type=EventType.SESSION_STARTED,
        session_id=session_id,
        sequence_number=latest_seq + 1,
        timestamp=datetime.utcnow(),
        data={"first_step_index": 0}
    )

    # Apply through engine
    result = engine.apply_event(state, event)

    # Save event and snapshot
    await append_and_snapshot(
        db=db,
        session_id=session_id,
        event_type=event.event_type,
        event_data=event.data,
        sequence_number=event.sequence_number,
        state=result.new_state
    )

    # Update session record
    session.status = "active"
    session.started_at = datetime.utcnow()
    session.current_step_index = result.new_state.current_step_index

    await db.commit()
    await db.refresh(session)

    # TODO Week 3: Execute LLM tasks if any
    # for task in result.llm_tasks:
    #     await execute_llm_task(task, state, db)

    return SessionStateResponse(
        session=session,
        ui_response=result.ui_response
    )


@router.post("/{session_id}/attempt", response_model=SessionStateResponse)
async def submit_attempt(
    session_id: str,
    payload: AttemptSubmission,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Submit an answer for grading.
    Routes to appropriate step handler for scoring.
    """
    # Load session
    result = await db.execute(
        select(GameSession).where(GameSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if session.status != "active":
        raise HTTPException(status_code=400, detail="Session not active")

    # Load challenge steps
    result = await db.execute(
        select(ChallengeStep)
        .where(ChallengeStep.challenge_id == session.challenge_id)
        .order_by(ChallengeStep.step_index)
    )
    steps = list(result.scalars().all())

    # Create engine
    engine = GameEngine(steps)

    # Hydrate current state
    state, latest_seq = await hydrate_state(
        db=db,
        session_id=session_id,
        challenge_id=session.challenge_id,
        user_id=current_user.id,
        engine=engine
    )

    # Get current step
    current_step = steps[state.current_step_index]

    # Get handler for this step type
    handler = get_handler_for_step_type(current_step.step_type)

    # Handle submission
    handler_result = handler.handle_submission(current_step, payload.answer, state)

    # Create USER_SUBMITTED_ANSWER event
    event = Event(
        event_type=EventType.USER_SUBMITTED_ANSWER,
        session_id=session_id,
        sequence_number=latest_seq + 1,
        timestamp=datetime.utcnow(),
        data={
            "step_index": state.current_step_index,
            "answer": payload.answer
        }
    )

    # Apply through engine
    engine_result = engine.apply_event(state, event)

    # Save event
    next_seq = event.sequence_number

    await append_and_snapshot(
        db=db,
        session_id=session_id,
        event_type=event.event_type,
        event_data=event.data,
        sequence_number=next_seq,
        state=engine_result.new_state
    )

    # If handler doesn't require LEM, score immediately
    if not handler_result.requires_lem and handler_result.score is not None:
        # Create SCORE_AWARDED event
        score_event = Event(
            event_type=EventType.SCORE_AWARDED,
            session_id=session_id,
            sequence_number=next_seq + 1,
            timestamp=datetime.utcnow(),
            data={
                "step_index": state.current_step_index,
                "score": handler_result.score,
                "max_possible": current_step.points_possible,
                "passed": handler_result.passed,
                "feedback": handler_result.feedback
            }
        )

        # Apply score event
        score_result = engine.apply_event(engine_result.new_state, score_event)

        await append_and_snapshot(
            db=db,
            session_id=session_id,
            event_type=score_event.event_type,
            event_data=score_event.data,
            sequence_number=score_event.sequence_number,
            state=score_result.new_state
        )

        # Add feedback message
        score_result.new_state.add_message(
            role="gm",
            content=handler_result.feedback or "Answer submitted.",
            timestamp=datetime.utcnow().isoformat()
        )

        # Update session record
        session.total_score = score_result.new_state.total_score
        session.current_step_index = score_result.new_state.current_step_index

        # Check if session complete
        if score_result.new_state.current_step_index >= len(steps):
            session.status = "completed"
            session.completed_at = datetime.utcnow()

        await db.commit()
        await db.refresh(session)

        return SessionStateResponse(
            session=session,
            ui_response=engine._build_ui_response(score_result.new_state, current_step)
        )

    # TODO Week 3: If requires LEM, request LLM evaluation
    # For now, just return state waiting for evaluation
    await db.commit()
    await db.refresh(session)

    return SessionStateResponse(
        session=session,
        ui_response=engine_result.ui_response
    )


@router.get("/{session_id}/state", response_model=SessionStateResponse)
async def get_session_state(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Get current session state by replaying events.
    """
    # Load session
    result = await db.execute(
        select(GameSession).where(GameSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Load challenge steps
    result = await db.execute(
        select(ChallengeStep)
        .where(ChallengeStep.challenge_id == session.challenge_id)
        .order_by(ChallengeStep.step_index)
    )
    steps = list(result.scalars().all())

    # Create engine
    engine = GameEngine(steps)

    # Hydrate state
    state, _ = await hydrate_state(
        db=db,
        session_id=session_id,
        challenge_id=session.challenge_id,
        user_id=current_user.id,
        engine=engine
    )

    # Get current step
    if state.current_step_index < len(steps):
        current_step = steps[state.current_step_index]
    else:
        current_step = steps[-1]  # Last step if completed

    return SessionStateResponse(
        session=session,
        ui_response=engine._build_ui_response(state, current_step)
    )
