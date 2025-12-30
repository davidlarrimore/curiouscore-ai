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
from .models import GameSession, ChallengeStep, User, Challenge
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
from .game_engine.llm_orchestrator import LLMOrchestrator, LEMEvaluation
from .event_store import (
    append_event,
    hydrate_state,
    append_and_snapshot,
)


router = APIRouter(prefix="/sessions", tags=["sessions"])


# ============================================================================
# Helper Functions
# ============================================================================

async def execute_llm_tasks(
    tasks: list[dict],
    state: SessionState,
    steps: list[ChallengeStep],
    db: AsyncSession,
    engine: GameEngine
) -> tuple[SessionState, list[Event]]:
    """
    Execute LLM tasks and apply results to state.

    Args:
        tasks: List of LLM task dicts from engine
        state: Current session state
        steps: Challenge steps
        db: Database session
        engine: Game engine instance

    Returns:
        (updated_state, derived_events) tuple
    """
    orchestrator = LLMOrchestrator()
    derived_events = []
    current_state = state

    for task in tasks:
        task_type = task.get("task_type")

        if task_type == "GM_NARRATE":
            # Execute GM narration
            try:
                context = engine._build_gm_context(
                    current_state,
                    steps[task.get("step_index", 0)]
                )
                # For Simple challenges, include user_answer and message history
                if "user_answer" in task:
                    context["user_answer"] = task["user_answer"]
                # Include message history for conversational context
                context["messages"] = current_state.messages

                narration = await orchestrator.narrate_gm(context)

                # Create GM_NARRATED event
                gm_event = Event(
                    event_type=EventType.GM_NARRATED,
                    session_id=current_state.session_id,
                    sequence_number=task.get("sequence_number", 0),
                    timestamp=datetime.utcnow(),
                    data={"content": narration}
                )
                derived_events.append(gm_event)

                # Apply event to state
                result = engine.apply_event(current_state, gm_event)
                current_state = result.new_state

            except Exception as e:
                # GM narration failed - create event with error message
                error_message = str(e)
                if "API key" in error_message or "not configured" in error_message:
                    error_message = "LLM API not configured. Continuing without narration."

                gm_event = Event(
                    event_type=EventType.GM_NARRATED,
                    session_id=current_state.session_id,
                    sequence_number=task.get("sequence_number", 0),
                    timestamp=datetime.utcnow(),
                    data={"content": f"⚠️ Narration unavailable: {error_message}"}
                )
                derived_events.append(gm_event)

                result = engine.apply_event(current_state, gm_event)
                current_state = result.new_state

        elif task_type == "LEM_EVALUATE":
            # Execute LEM evaluation
            answer = task.get("answer", "")
            rubric = task.get("rubric", {})
            step_index = task.get("step_index", 0)
            step = steps[step_index]

            context = {
                "step_title": step.title,
                "step_instruction": step.instruction,
            }

            try:
                evaluation = await orchestrator.evaluate_lem(answer, rubric, context)

                # Create LEM_EVALUATED event
                lem_event = Event(
                    event_type=EventType.LEM_EVALUATED,
                    session_id=current_state.session_id,
                    sequence_number=task.get("sequence_number", 0),
                    timestamp=datetime.utcnow(),
                    data={
                        "raw_score": evaluation.raw_score,
                        "rationale": evaluation.rationale,
                        "criteria_scores": evaluation.criteria_scores,
                        "passed": evaluation.passed,
                        "step_index": step_index
                    }
                )
                derived_events.append(lem_event)

                # Apply event to state (engine enforces score clamping)
                result = engine.apply_event(current_state, lem_event)
                current_state = result.new_state

            except Exception as e:
                # LEM evaluation failed (API error, invalid JSON, etc.)
                # Create LEM_EVALUATED event with 0 score and error message
                error_message = str(e)

                # Provide helpful error message for common issues
                if "API key" in error_message or "not configured" in error_message:
                    error_message = "LLM API key not configured. Please set ANTHROPIC_API_KEY, OPENAI_API_KEY, or GEMINI_API_KEY in your .env file."
                elif "Invalid JSON" in error_message or "JSONDecodeError" in error_message:
                    error_message = f"LLM returned invalid response format: {error_message}"

                lem_event = Event(
                    event_type=EventType.LEM_EVALUATED,
                    session_id=current_state.session_id,
                    sequence_number=task.get("sequence_number", 0),
                    timestamp=datetime.utcnow(),
                    data={
                        "raw_score": 0,
                        "rationale": f"⚠️ Evaluation Error: {error_message}",
                        "criteria_scores": {},
                        "passed": False,
                        "step_index": step_index
                    }
                )
                derived_events.append(lem_event)

                result = engine.apply_event(current_state, lem_event)
                current_state = result.new_state

        elif task_type == "TEACH_HINTS":
            # Execute hint generation
            try:
                context = engine._build_hint_context(
                    current_state,
                    steps[task.get("step_index", 0)]
                )
                hint = await orchestrator.generate_hint(context)

                # Create HINT_PROVIDED event (using GM_NARRATED event type with metadata)
                hint_event = Event(
                    event_type=EventType.GM_NARRATED,
                    session_id=current_state.session_id,
                    sequence_number=task.get("sequence_number", 0),
                    timestamp=datetime.utcnow(),
                    data={
                        "content": f"💡 Hint: {hint}",
                        "is_hint": True
                    }
                )
                derived_events.append(hint_event)

                # Apply event to state
                result = engine.apply_event(current_state, hint_event)
                current_state = result.new_state

            except Exception as e:
                # Hint generation failed - provide fallback message
                error_message = str(e)
                if "API key" in error_message or "not configured" in error_message:
                    error_message = "Hint service unavailable. Try solving the problem step by step."

                hint_event = Event(
                    event_type=EventType.GM_NARRATED,
                    session_id=current_state.session_id,
                    sequence_number=task.get("sequence_number", 0),
                    timestamp=datetime.utcnow(),
                    data={
                        "content": f"⚠️ {error_message}",
                        "is_hint": True
                    }
                )
                derived_events.append(hint_event)

                result = engine.apply_event(current_state, hint_event)
                current_state = result.new_state

    return current_state, derived_events


async def load_challenge_steps(
    challenge_id: str,
    db: AsyncSession
) -> tuple[Challenge, list[ChallengeStep]]:
    """
    Load challenge and its steps.
    For simple challenges, create a synthetic step from system_prompt.
    For advanced challenges, return the configured steps.

    Args:
        challenge_id: Challenge ID
        db: Database session

    Returns:
        (challenge, steps) tuple

    Raises:
        HTTPException: If challenge not found or has no steps/system_prompt
    """
    # Load challenge
    result = await db.execute(
        select(Challenge).where(Challenge.id == challenge_id)
    )
    challenge = result.scalar_one_or_none()

    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    # Load steps
    result = await db.execute(
        select(ChallengeStep)
        .where(ChallengeStep.challenge_id == challenge_id)
        .order_by(ChallengeStep.step_index)
    )
    steps = list(result.scalars().all())

    # For simple challenges, create synthetic step from system_prompt
    if challenge.challenge_type == "simple":
        if not steps:
            # Get progress config from custom_variables if present
            progress_config = None
            if challenge.custom_variables and "progress_tracking" in challenge.custom_variables:
                progress_config = challenge.custom_variables["progress_tracking"]

            # Inject metadata requirements into the system prompt
            from .prompt_injection import inject_metadata_requirements
            enhanced_prompt = inject_metadata_requirements(
                challenge.system_prompt or "You are a helpful teaching assistant.",
                challenge.title,
                challenge.xp_reward,
                challenge.passing_score,
                progress_config
            )

            # Create a synthetic step with a user-friendly instruction
            # The actual system prompt will be used by the LLM but not shown to users
            # Set auto_narrate=True to trigger teaching on entry
            synthetic_step = ChallengeStep(
                id=f"synthetic-{challenge_id}",
                challenge_id=challenge_id,
                step_index=0,
                step_type="CHAT",
                title=challenge.title,
                instruction=f"Complete the {challenge.title} challenge. Use the chat below to interact with the AI instructor.",
                points_possible=100,
                passing_threshold=challenge.passing_score,
                rubric=None,
                auto_narrate=True,  # Enable auto-teaching for simple challenges
                options=None,
                correct_answer=None,
                correct_answers=None,
                gm_context=enhanced_prompt  # Full teaching prompt WITH metadata requirements injected
            )
            steps = [synthetic_step]
    else:
        # Advanced challenge must have steps configured
        if not steps:
            raise HTTPException(
                status_code=400,
                detail="Advanced challenge has no steps configured"
            )

    return challenge, steps


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

    # Load challenge and steps (handles simple vs advanced)
    challenge, steps = await load_challenge_steps(session.challenge_id, db)

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

    # Execute LLM tasks if any (Week 3)
    if result.llm_tasks:
        updated_state, llm_events = await execute_llm_tasks(
            tasks=result.llm_tasks,
            state=result.new_state,
            steps=steps,
            db=db,
            engine=engine
        )

        # Save LLM events (starting from event.sequence_number + 1)
        for idx, llm_event in enumerate(llm_events):
            await append_and_snapshot(
                db=db,
                session_id=session_id,
                event_type=llm_event.event_type,
                event_data=llm_event.data,
                sequence_number=event.sequence_number + 1 + idx,
                state=updated_state
            )

        # Use updated state for UI response
        result.new_state = updated_state
        # Rebuild UI response to include new messages from LLM tasks
        current_step = steps[result.new_state.current_step_index]
        result.ui_response = engine._build_ui_response(result.new_state, current_step)

    await db.commit()
    await db.refresh(session)

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

    # Load challenge and steps (handles simple vs advanced)
    challenge, steps = await load_challenge_steps(session.challenge_id, db)

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

    # Save event and updated state
    await append_and_snapshot(
        db=db,
        session_id=session_id,
        event_type=event.event_type,
        event_data=event.data,
        sequence_number=event.sequence_number,
        state=engine_result.new_state
    )

    # Execute LLM tasks if handler provided them (for both Simple and Advanced challenges)
    if handler_result.llm_tasks:
        updated_state, llm_events = await execute_llm_tasks(
            tasks=handler_result.llm_tasks,
            state=engine_result.new_state,
            steps=steps,
            db=db,
            engine=engine
        )

        # Save LLM events (starting from event.sequence_number + 1)
        for idx, llm_event in enumerate(llm_events):
            await append_and_snapshot(
                db=db,
                session_id=session_id,
                event_type=llm_event.event_type,
                event_data=llm_event.data,
                sequence_number=event.sequence_number + 1 + idx,
                state=updated_state
            )

        # Update session record
        session.total_score = updated_state.total_score
        session.current_step_index = updated_state.current_step_index

        # Check if session complete
        if updated_state.status == "completed":
            session.status = "completed"
            session.completed_at = datetime.utcnow()

        await db.commit()
        await db.refresh(session)

        # Get current step for UI response
        if updated_state.current_step_index < len(steps):
            current_step_for_ui = steps[updated_state.current_step_index]
        else:
            current_step_for_ui = steps[-1]

        return SessionStateResponse(
            session=session,
            ui_response=engine._build_ui_response(updated_state, current_step_for_ui)
        )

    # No LEM required - return as-is
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

    # Load challenge and steps (handles simple vs advanced)
    challenge, steps = await load_challenge_steps(session.challenge_id, db)

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


@router.post("/{session_id}/action", response_model=SessionStateResponse)
async def submit_action(
    session_id: str,
    payload: ActionSubmission,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Submit a non-graded action (continue, hint, etc.).

    Actions:
    - "continue": Advance through CONTINUE_GATE step
    - "hint": Request a hint from TEACH_HINTS LLM task
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

    # Load challenge and steps (handles simple vs advanced)
    challenge, steps = await load_challenge_steps(session.challenge_id, db)

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

    action = payload.action.lower()

    # Handle different action types
    if action == "continue":
        # Create USER_CONTINUED event
        event = Event(
            event_type=EventType.USER_CONTINUED,
            session_id=session_id,
            sequence_number=latest_seq + 1,
            timestamp=datetime.utcnow(),
            data={"action": "continue"}
        )

        # Apply through engine
        result = engine.apply_event(state, event)

        # Save event
        await append_and_snapshot(
            db=db,
            session_id=session_id,
            event_type=event.event_type,
            event_data=event.data,
            sequence_number=event.sequence_number,
            state=result.new_state
        )

        # Update session record
        session.current_step_index = result.new_state.current_step_index

        if result.new_state.status == "completed":
            session.status = "completed"
            session.completed_at = datetime.utcnow()

        await db.commit()
        await db.refresh(session)

        # Get current step for UI response
        if result.new_state.current_step_index < len(steps):
            current_step = steps[result.new_state.current_step_index]
        else:
            current_step = steps[-1]

        return SessionStateResponse(
            session=session,
            ui_response=engine._build_ui_response(result.new_state, current_step)
        )

    elif action == "hint":
        # Create USER_REQUESTED_HINT event
        event = Event(
            event_type=EventType.USER_REQUESTED_HINT,
            session_id=session_id,
            sequence_number=latest_seq + 1,
            timestamp=datetime.utcnow(),
            data={"action": "hint"}
        )

        # Apply through engine (generates LLM task)
        result = engine.apply_event(state, event)

        # Save event
        await append_and_snapshot(
            db=db,
            session_id=session_id,
            event_type=event.event_type,
            event_data=event.data,
            sequence_number=event.sequence_number,
            state=result.new_state
        )

        # Execute LLM tasks if any (TEACH_HINTS)
        if result.llm_tasks:
            updated_state, llm_events = await execute_llm_tasks(
                tasks=result.llm_tasks,
                state=result.new_state,
                steps=steps,
                db=db,
                engine=engine
            )

            # Save LLM events
            for idx, llm_event in enumerate(llm_events):
                await append_and_snapshot(
                    db=db,
                    session_id=session_id,
                    event_type=llm_event.event_type,
                    event_data=llm_event.data,
                    sequence_number=event.sequence_number + 1 + idx,
                    state=updated_state
                )

            result.new_state = updated_state

        await db.commit()
        await db.refresh(session)

        current_step = steps[result.new_state.current_step_index]

        return SessionStateResponse(
            session=session,
            ui_response=engine._build_ui_response(result.new_state, current_step)
        )

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown action: {action}. Valid actions: continue, hint"
        )
