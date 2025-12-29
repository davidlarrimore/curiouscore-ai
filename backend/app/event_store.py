"""
Event Store

Handles event persistence and state hydration.
Implements event sourcing pattern with snapshots for performance.

Key Responsibilities:
- Append events to database (append-only log)
- Load latest snapshot for a session
- Replay events from snapshot forward to hydrate state
- Create snapshots periodically (every N events)

Event Sourcing Flow:
1. Load latest snapshot (if exists)
2. Replay events since snapshot
3. Apply new event
4. Save new snapshot if needed (every SNAPSHOT_INTERVAL events)
"""

import uuid
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from .models import GameEvent, SessionSnapshot
from .game_engine.state import SessionState
from .game_engine.events import Event, EventType


# Create snapshot every N events
SNAPSHOT_INTERVAL = 5


async def append_event(
    db: AsyncSession,
    session_id: str,
    event_type: EventType,
    event_data: dict,
    sequence_number: int
) -> GameEvent:
    """
    Append an event to the event log.

    Args:
        db: Database session
        session_id: Session ID
        event_type: Type of event
        event_data: Event payload
        sequence_number: Sequence number for this event

    Returns:
        Created GameEvent
    """
    event = GameEvent(
        id=str(uuid.uuid4()),
        session_id=session_id,
        event_type=event_type.value if isinstance(event_type, EventType) else event_type,
        event_data=event_data,
        sequence_number=sequence_number
    )

    db.add(event)
    await db.flush()

    return event


async def get_latest_snapshot(
    db: AsyncSession,
    session_id: str
) -> Optional[Tuple[SessionState, int]]:
    """
    Get the latest snapshot for a session.

    Args:
        db: Database session
        session_id: Session ID

    Returns:
        (SessionState, event_sequence) tuple, or None if no snapshot exists
    """
    result = await db.execute(
        select(SessionSnapshot)
        .where(SessionSnapshot.session_id == session_id)
        .order_by(SessionSnapshot.event_sequence.desc())
        .limit(1)
    )

    snapshot = result.scalar_one_or_none()

    if snapshot is None:
        return None

    # Deserialize state from JSON
    state = SessionState(**snapshot.snapshot_data)

    return (state, snapshot.event_sequence)


async def get_events_since(
    db: AsyncSession,
    session_id: str,
    since_sequence: int = -1
) -> List[GameEvent]:
    """
    Get all events for a session since a given sequence number.

    Args:
        db: Database session
        session_id: Session ID
        since_sequence: Get events after this sequence number (-1 for all events)

    Returns:
        List of GameEvent objects, ordered by sequence_number
    """
    query = (
        select(GameEvent)
        .where(
            and_(
                GameEvent.session_id == session_id,
                GameEvent.sequence_number > since_sequence
            )
        )
        .order_by(GameEvent.sequence_number)
    )

    result = await db.execute(query)
    return list(result.scalars().all())


async def hydrate_state(
    db: AsyncSession,
    session_id: str,
    challenge_id: str,
    user_id: str,
    engine
) -> Tuple[SessionState, int]:
    """
    Hydrate current session state by loading snapshot and replaying events.

    Args:
        db: Database session
        session_id: Session ID
        challenge_id: Challenge ID
        user_id: User ID
        engine: GameEngine instance to replay events through

    Returns:
        (SessionState, latest_sequence_number) tuple
    """
    # Try to load latest snapshot
    snapshot_data = await get_latest_snapshot(db, session_id)

    if snapshot_data:
        state, snapshot_sequence = snapshot_data
        since_sequence = snapshot_sequence
    else:
        # No snapshot - start with initial state
        state = SessionState(
            session_id=session_id,
            challenge_id=challenge_id,
            user_id=user_id,
            status="created"
        )
        since_sequence = -1

    # Get events since snapshot
    events = await get_events_since(db, session_id, since_sequence)

    # Replay events through engine
    for game_event in events:
        # Convert GameEvent to Event
        event = Event(
            event_type=EventType(game_event.event_type),
            session_id=game_event.session_id,
            sequence_number=game_event.sequence_number,
            timestamp=game_event.created_at if isinstance(game_event.created_at, datetime) else datetime.fromisoformat(game_event.created_at),
            data=game_event.event_data
        )

        # Apply through engine
        result = engine.apply_event(state, event)
        state = result.new_state

    # Return current state and latest sequence number
    latest_sequence = events[-1].sequence_number if events else since_sequence

    return (state, latest_sequence)


async def create_snapshot(
    db: AsyncSession,
    session_id: str,
    state: SessionState,
    event_sequence: int
):
    """
    Create a snapshot of current session state.

    Args:
        db: Database session
        session_id: Session ID
        state: Current SessionState to snapshot
        event_sequence: Event sequence number this snapshot is valid up to
    """
    snapshot = SessionSnapshot(
        id=str(uuid.uuid4()),
        session_id=session_id,
        snapshot_data=state.model_dump(),
        event_sequence=event_sequence
    )

    db.add(snapshot)
    await db.flush()


async def should_create_snapshot(
    db: AsyncSession,
    session_id: str,
    current_sequence: int
) -> bool:
    """
    Determine if we should create a snapshot.
    Creates snapshots every SNAPSHOT_INTERVAL events.

    Args:
        db: Database session
        session_id: Session ID
        current_sequence: Current event sequence number

    Returns:
        True if snapshot should be created
    """
    # Always create snapshot at sequence 0 (session start)
    if current_sequence == 0:
        return True

    # Create every SNAPSHOT_INTERVAL events
    if current_sequence % SNAPSHOT_INTERVAL == 0:
        return True

    return False


async def append_and_snapshot(
    db: AsyncSession,
    session_id: str,
    event_type: EventType,
    event_data: dict,
    sequence_number: int,
    state: SessionState
) -> GameEvent:
    """
    Append an event and create snapshot if needed.

    Args:
        db: Database session
        session_id: Session ID
        event_type: Event type
        event_data: Event data
        sequence_number: Sequence number
        state: Current state after applying this event

    Returns:
        Created GameEvent
    """
    # Append event
    event = await append_event(db, session_id, event_type, event_data, sequence_number)

    # Create snapshot if needed
    if await should_create_snapshot(db, session_id, sequence_number):
        await create_snapshot(db, session_id, state, sequence_number)

    return event
