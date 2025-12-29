"""
Unit Tests for Game Engine

Tests the core game engine logic, event application, and state management.
"""

import pytest
from datetime import datetime
from app.game_engine.engine import GameEngine, EngineResult
from app.game_engine.events import Event, EventType
from app.game_engine.state import SessionState, DisplayMessage, StepScore
from app.models import ChallengeStep


@pytest.fixture
def sample_steps():
    """Create sample challenge steps for testing."""
    return [
        ChallengeStep(
            id="step-0",
            challenge_id="test-challenge",
            step_index=0,
            step_type="MCQ_SINGLE",
            title="Test MCQ",
            instruction="Select the correct answer",
            options=["Correct", "Wrong"],
            correct_answer=0,
            points_possible=50,
            passing_threshold=100,
            auto_narrate=False
        ),
        ChallengeStep(
            id="step-1",
            challenge_id="test-challenge",
            step_index=1,
            step_type="CONTINUE_GATE",
            title="Gate",
            instruction="Continue to next step",
            points_possible=0,
            passing_threshold=0,
            auto_narrate=False
        ),
        ChallengeStep(
            id="step-2",
            challenge_id="test-challenge",
            step_index=2,
            step_type="TRUE_FALSE",
            title="True/False",
            instruction="True or False",
            correct_answer=True,
            points_possible=50,
            passing_threshold=100,
            auto_narrate=False
        )
    ]


@pytest.fixture
def engine(sample_steps):
    """Create game engine with sample steps."""
    return GameEngine(sample_steps)


@pytest.fixture
def initial_state():
    """Create initial session state."""
    return SessionState(
        session_id="test-session",
        challenge_id="test-challenge",
        user_id="test-user",
        current_step_index=0,
        status="created",
        step_scores=[],
        total_score=0,
        max_possible_score=100,
        messages=[],
        current_ui_mode="",
        context_summary=""
    )


# ============================================================================
# Session Lifecycle Tests
# ============================================================================

def test_session_started_event(engine, initial_state):
    """Test SESSION_STARTED event initializes state correctly."""
    event = Event(
        event_type=EventType.SESSION_STARTED,
        session_id="test-session",
        sequence_number=1,
        timestamp=datetime.utcnow(),
        data={}
    )

    result = engine.apply_event(initial_state, event)

    assert result.new_state.status == "active"
    assert result.new_state.current_step_index == 0
    assert result.new_state.current_ui_mode == "MCQ_SINGLE"
    assert len(result.derived_events) == 1
    assert result.derived_events[0].event_type == EventType.STEP_ENTERED


def test_session_created_event(engine, initial_state):
    """Test SESSION_CREATED is a no-op audit event."""
    event = Event(
        event_type=EventType.SESSION_CREATED,
        session_id="test-session",
        sequence_number=0,
        timestamp=datetime.utcnow(),
        data={}
    )

    result = engine.apply_event(initial_state, event)

    # State unchanged (audit event only)
    assert result.new_state.status == initial_state.status
    assert len(result.derived_events) == 0


# ============================================================================
# MCQ Tests
# ============================================================================

def test_mcq_correct_answer_advances(engine, initial_state):
    """Test correct MCQ answer awards points and advances."""
    # Start session first
    start_event = Event(
        event_type=EventType.SESSION_STARTED,
        session_id="test-session",
        sequence_number=1,
        timestamp=datetime.utcnow(),
        data={}
    )
    active_state = engine.apply_event(initial_state, start_event).new_state

    # Submit correct answer
    submit_event = Event(
        event_type=EventType.USER_SUBMITTED_ANSWER,
        session_id="test-session",
        sequence_number=2,
        timestamp=datetime.utcnow(),
        data={"step_index": 0, "answer": 0}
    )

    result = engine.apply_event(active_state, submit_event)

    assert result.new_state.total_score == 50
    assert result.new_state.current_step_index == 1  # Advanced
    assert len(result.new_state.step_scores) == 1
    assert result.new_state.step_scores[0].points_earned == 50


def test_mcq_wrong_answer_stays_on_step(engine, initial_state):
    """Test wrong MCQ answer doesn't advance."""
    start_event = Event(
        event_type=EventType.SESSION_STARTED,
        session_id="test-session",
        sequence_number=1,
        timestamp=datetime.utcnow(),
        data={}
    )
    active_state = engine.apply_event(initial_state, start_event).new_state

    submit_event = Event(
        event_type=EventType.USER_SUBMITTED_ANSWER,
        session_id="test-session",
        sequence_number=2,
        timestamp=datetime.utcnow(),
        data={"step_index": 0, "answer": 1}  # Wrong answer
    )

    result = engine.apply_event(active_state, submit_event)

    assert result.new_state.total_score == 0
    assert result.new_state.current_step_index == 0  # Stayed on step
    assert len(result.new_state.step_scores) == 0


def test_mcq_multi_correct(engine):
    """Test MCQ_MULTI with all correct answers."""
    steps = [
        ChallengeStep(
            id="step-0",
            challenge_id="test-challenge",
            step_index=0,
            step_type="MCQ_MULTI",
            title="Multi",
            instruction="Select all",
            options=["A", "B", "C"],
            correct_answers=[0, 2],
            points_possible=40,
            passing_threshold=100,
            auto_narrate=False
        )
    ]
    engine = GameEngine(steps)

    state = SessionState(
        session_id="test-session",
        challenge_id="test-challenge",
        user_id="test-user",
        current_step_index=0,
        status="active",
        step_scores=[],
        total_score=0,
        max_possible_score=40,
        messages=[],
        current_ui_mode="MCQ_MULTI",
        context_summary=""
    )

    submit_event = Event(
        event_type=EventType.USER_SUBMITTED_ANSWER,
        session_id="test-session",
        sequence_number=1,
        timestamp=datetime.utcnow(),
        data={"step_index": 0, "answer": [0, 2]}
    )

    result = engine.apply_event(state, submit_event)

    assert result.new_state.total_score == 40
    assert result.new_state.status == "completed"  # Last step


def test_mcq_multi_partial_credit(engine):
    """Test MCQ_MULTI with partial credit."""
    steps = [
        ChallengeStep(
            id="step-0",
            challenge_id="test-challenge",
            step_index=0,
            step_type="MCQ_MULTI",
            title="Multi",
            instruction="Select all",
            options=["A", "B", "C"],
            correct_answers=[0, 2],
            points_possible=40,
            passing_threshold=100,
            auto_narrate=False
        )
    ]
    engine = GameEngine(steps)

    state = SessionState(
        session_id="test-session",
        challenge_id="test-challenge",
        user_id="test-user",
        current_step_index=0,
        status="active",
        step_scores=[],
        total_score=0,
        max_possible_score=40,
        messages=[],
        current_ui_mode="MCQ_MULTI",
        context_summary=""
    )

    submit_event = Event(
        event_type=EventType.USER_SUBMITTED_ANSWER,
        session_id="test-session",
        sequence_number=1,
        timestamp=datetime.utcnow(),
        data={"step_index": 0, "answer": [0]}  # Only 1 of 2 correct
    )

    result = engine.apply_event(state, submit_event)

    # Gets 50% of points (1/2 correct)
    assert result.new_state.total_score == 20
    # Doesn't advance (needs 100% to pass threshold)
    assert result.new_state.current_step_index == 0


# ============================================================================
# TRUE_FALSE Tests
# ============================================================================

def test_true_false_correct(engine):
    """Test TRUE_FALSE with correct answer."""
    steps = [
        ChallengeStep(
            id="step-0",
            challenge_id="test-challenge",
            step_index=0,
            step_type="TRUE_FALSE",
            title="T/F",
            instruction="True or False",
            correct_answer=True,
            points_possible=25,
            passing_threshold=100,
            auto_narrate=False
        )
    ]
    engine = GameEngine(steps)

    state = SessionState(
        session_id="test-session",
        challenge_id="test-challenge",
        user_id="test-user",
        current_step_index=0,
        status="active",
        step_scores=[],
        total_score=0,
        max_possible_score=25,
        messages=[],
        current_ui_mode="TRUE_FALSE",
        context_summary=""
    )

    submit_event = Event(
        event_type=EventType.USER_SUBMITTED_ANSWER,
        session_id="test-session",
        sequence_number=1,
        timestamp=datetime.utcnow(),
        data={"step_index": 0, "answer": True}
    )

    result = engine.apply_event(state, submit_event)

    assert result.new_state.total_score == 25
    assert result.new_state.status == "completed"


# ============================================================================
# CONTINUE_GATE Tests
# ============================================================================

def test_continue_gate_advances(engine, initial_state):
    """Test USER_CONTINUED advances through gate."""
    start_event = Event(
        event_type=EventType.SESSION_STARTED,
        session_id="test-session",
        sequence_number=1,
        timestamp=datetime.utcnow(),
        data={}
    )
    active_state = engine.apply_event(initial_state, start_event).new_state

    # Advance to gate (step 1)
    submit_event = Event(
        event_type=EventType.USER_SUBMITTED_ANSWER,
        session_id="test-session",
        sequence_number=2,
        timestamp=datetime.utcnow(),
        data={"step_index": 0, "answer": 0}
    )
    at_gate_state = engine.apply_event(active_state, submit_event).new_state

    # Continue through gate
    continue_event = Event(
        event_type=EventType.USER_CONTINUED,
        session_id="test-session",
        sequence_number=3,
        timestamp=datetime.utcnow(),
        data={"action": "continue"}
    )

    result = engine.apply_event(at_gate_state, continue_event)

    assert result.new_state.current_step_index == 2  # Advanced
    assert result.new_state.current_ui_mode == "TRUE_FALSE"


# ============================================================================
# Hint Request Tests
# ============================================================================

def test_hint_request_generates_task(engine, initial_state):
    """Test USER_REQUESTED_HINT generates TEACH_HINTS task."""
    start_event = Event(
        event_type=EventType.SESSION_STARTED,
        session_id="test-session",
        sequence_number=1,
        timestamp=datetime.utcnow(),
        data={}
    )
    active_state = engine.apply_event(initial_state, start_event).new_state

    hint_event = Event(
        event_type=EventType.USER_REQUESTED_HINT,
        session_id="test-session",
        sequence_number=2,
        timestamp=datetime.utcnow(),
        data={"action": "hint"}
    )

    result = engine.apply_event(active_state, hint_event)

    assert len(result.llm_tasks) == 1
    assert result.llm_tasks[0]["task_type"] == "TEACH_HINTS"


# ============================================================================
# Completion Tests
# ============================================================================

def test_completing_last_step_marks_completed(engine, initial_state):
    """Test completing the last step marks session as completed."""
    # Start and advance to last step (step 2)
    start_event = Event(
        event_type=EventType.SESSION_STARTED,
        session_id="test-session",
        sequence_number=1,
        timestamp=datetime.utcnow(),
        data={}
    )
    state = engine.apply_event(initial_state, start_event).new_state

    # Complete step 0
    state = engine.apply_event(state, Event(
        event_type=EventType.USER_SUBMITTED_ANSWER,
        session_id="test-session",
        sequence_number=2,
        timestamp=datetime.utcnow(),
        data={"step_index": 0, "answer": 0}
    )).new_state

    # Continue through gate (step 1)
    state = engine.apply_event(state, Event(
        event_type=EventType.USER_CONTINUED,
        session_id="test-session",
        sequence_number=3,
        timestamp=datetime.utcnow(),
        data={"action": "continue"}
    )).new_state

    # Complete final step (step 2)
    result = engine.apply_event(state, Event(
        event_type=EventType.USER_SUBMITTED_ANSWER,
        session_id="test-session",
        sequence_number=4,
        timestamp=datetime.utcnow(),
        data={"step_index": 2, "answer": True}
    ))

    assert result.new_state.status == "completed"
    assert result.new_state.total_score == 100


# ============================================================================
# State Management Tests
# ============================================================================

def test_state_add_message():
    """Test adding messages to state."""
    state = SessionState(
        session_id="test",
        challenge_id="test",
        user_id="test",
        current_step_index=0,
        status="active",
        step_scores=[],
        total_score=0,
        max_possible_score=100,
        messages=[],
        current_ui_mode="",
        context_summary=""
    )

    state.add_message("user", "Test message", datetime.utcnow().isoformat())

    assert len(state.messages) == 1
    assert state.messages[0].role == "user"
    assert state.messages[0].content == "Test message"


def test_state_update_context_summary():
    """Test updating context summary."""
    state = SessionState(
        session_id="test",
        challenge_id="test",
        user_id="test",
        current_step_index=0,
        status="active",
        step_scores=[],
        total_score=0,
        max_possible_score=100,
        messages=[],
        current_ui_mode="",
        context_summary=""
    )

    state.update_context_summary("New summary")

    assert state.context_summary == "New summary"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
