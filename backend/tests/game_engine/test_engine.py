"""
Unit tests for GameEngine.

Tests engine initialization, event application, and orchestration.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

from app.game_engine.engine import GameEngine, EngineResult
from app.game_engine.events import Event, EventType
from app.game_engine.state import SessionState, StepScore
from app.models import ChallengeStep


class TestGameEngineInitialization:
    """Test GameEngine initialization."""

    def test_create_engine_with_steps(self):
        """Test creating engine with challenge steps."""
        steps = [
            Mock(spec=ChallengeStep, step_index=0, step_type="MCQ_SINGLE", title="Step 1"),
            Mock(spec=ChallengeStep, step_index=1, step_type="CHAT", title="Step 2"),
            Mock(spec=ChallengeStep, step_index=2, step_type="CONTINUE_GATE", title="Step 3"),
        ]

        engine = GameEngine(steps)

        assert engine.total_steps == 3
        assert len(engine.steps) == 3

    def test_engine_sorts_steps_by_index(self):
        """Test that engine sorts steps by step_index."""
        # Steps in wrong order
        steps = [
            Mock(spec=ChallengeStep, step_index=2, step_type="CHAT", title="Step 3"),
            Mock(spec=ChallengeStep, step_index=0, step_type="MCQ_SINGLE", title="Step 1"),
            Mock(spec=ChallengeStep, step_index=1, step_type="CONTINUE_GATE", title="Step 2"),
        ]

        engine = GameEngine(steps)

        # Should be sorted
        assert engine.steps[0].step_index == 0
        assert engine.steps[1].step_index == 1
        assert engine.steps[2].step_index == 2


class TestSessionStarted:
    """Test SESSION_STARTED event handling."""

    def test_session_started_enters_first_step(self):
        """Test that SESSION_STARTED enters the first step."""
        steps = [
            Mock(
                spec=ChallengeStep,
                step_index=0,
                step_type="MCQ_SINGLE",
                title="First Step",
                auto_narrate=False,
                instruction="Select the correct answer"
            ),
        ]

        engine = GameEngine(steps)

        state = SessionState(
            session_id="test-session",
            challenge_id="test-challenge",
            user_id="test-user",
            status="created"
        )

        event = Event(
            event_type=EventType.SESSION_STARTED,
            session_id="test-session",
            sequence_number=1,
            timestamp=datetime.utcnow(),
            data={"first_step_index": 0}
        )

        result = engine.apply_event(state, event)

        # Check new state
        assert result.new_state.status == "active"
        assert result.new_state.current_step_index == 0
        assert result.new_state.current_ui_mode == "MCQ_SINGLE"

        # Check derived events
        assert len(result.derived_events) == 1
        assert result.derived_events[0].event_type == EventType.STEP_ENTERED

    def test_session_started_requests_gm_narration_if_enabled(self):
        """Test that GM narration is requested when auto_narrate is true."""
        steps = [
            Mock(
                spec=ChallengeStep,
                step_index=0,
                step_type="CHAT",
                title="Welcome",
                auto_narrate=True,
                gm_context="Welcome the user",
                instruction="Let's get started"
            ),
        ]

        engine = GameEngine(steps)

        state = SessionState(
            session_id="test-session",
            challenge_id="test-challenge",
            user_id="test-user"
        )

        event = Event(
            event_type=EventType.SESSION_STARTED,
            session_id="test-session",
            sequence_number=1,
            timestamp=datetime.utcnow(),
            data={}
        )

        result = engine.apply_event(state, event)

        # Should have LLM task for GM narration
        assert len(result.llm_tasks) == 1
        assert result.llm_tasks[0]["task_type"] == "GM_NARRATE"
        assert result.llm_tasks[0]["step_index"] == 0

    def test_session_started_no_gm_narration_if_disabled(self):
        """Test that GM narration is not requested when auto_narrate is false."""
        steps = [
            Mock(
                spec=ChallengeStep,
                step_index=0,
                step_type="MCQ_SINGLE",
                title="Question 1",
                auto_narrate=False,
                instruction="Pick one"
            ),
        ]

        engine = GameEngine(steps)

        state = SessionState(
            session_id="test-session",
            challenge_id="test-challenge",
            user_id="test-user"
        )

        event = Event(
            event_type=EventType.SESSION_STARTED,
            session_id="test-session",
            sequence_number=1,
            timestamp=datetime.utcnow(),
            data={}
        )

        result = engine.apply_event(state, event)

        # Should NOT have LLM tasks
        assert len(result.llm_tasks) == 0


class TestUserSubmission:
    """Test USER_SUBMITTED_ANSWER event handling."""

    def test_user_submission_adds_user_message(self):
        """Test that user submission adds message to state."""
        steps = [
            Mock(
                spec=ChallengeStep,
                step_index=0,
                step_type="CHAT",
                title="Question",
                instruction="Answer the question"
            ),
        ]

        engine = GameEngine(steps)

        state = SessionState(
            session_id="test-session",
            challenge_id="test-challenge",
            user_id="test-user",
            current_step_index=0,
            current_ui_mode="CHAT"
        )

        event = Event(
            event_type=EventType.USER_SUBMITTED_ANSWER,
            session_id="test-session",
            sequence_number=2,
            timestamp=datetime.utcnow(),
            data={"answer": "This is my answer", "step_index": 0}
        )

        result = engine.apply_event(state, event)

        # Should add user message
        assert len(result.new_state.messages) == 1
        assert result.new_state.messages[0].role == "user"
        assert result.new_state.messages[0].content == "This is my answer"


class TestGMNarration:
    """Test GM_NARRATED event handling."""

    def test_gm_narration_adds_message(self):
        """Test that GM narration adds message to state."""
        steps = [
            Mock(
                spec=ChallengeStep,
                step_index=0,
                step_type="CHAT",
                title="Welcome",
                instruction="Get started"
            ),
        ]

        engine = GameEngine(steps)

        state = SessionState(
            session_id="test-session",
            challenge_id="test-challenge",
            user_id="test-user",
            current_step_index=0
        )

        event = Event(
            event_type=EventType.GM_NARRATED,
            session_id="test-session",
            sequence_number=3,
            timestamp=datetime.utcnow(),
            data={
                "content": "Welcome to the challenge! Let's begin.",
                "step_index": 0,
                "task_type": "introduction"
            }
        )

        result = engine.apply_event(state, event)

        # Should add GM message
        assert len(result.new_state.messages) == 1
        assert result.new_state.messages[0].role == "gm"
        assert "Welcome" in result.new_state.messages[0].content


class TestLEMEvaluation:
    """Test LEM_EVALUATED event handling."""

    def test_lem_evaluation_awards_clamped_score(self):
        """Test that engine clamps LEM score."""
        steps = [
            Mock(
                spec=ChallengeStep,
                step_index=0,
                step_type="CHAT",
                title="Question",
                instruction="Answer",
                points_possible=10,
                passing_threshold=70  # 70%
            ),
        ]

        engine = GameEngine(steps)

        state = SessionState(
            session_id="test-session",
            challenge_id="test-challenge",
            user_id="test-user",
            current_step_index=0,
            max_possible_score=10
        )

        # LEM gives 12 points, but max is 10
        event = Event(
            event_type=EventType.LEM_EVALUATED,
            session_id="test-session",
            sequence_number=4,
            timestamp=datetime.utcnow(),
            data={
                "raw_score": 12,  # LEM gave too much
                "clamped_score": 10,  # Engine should clamp to max
                "max_score": 10,
                "passed": True,
                "rationale": "Excellent answer!",
                "tags": ["correct"],
                "step_index": 0
            }
        )

        result = engine.apply_event(state, event)

        # Engine should award clamped score
        assert result.new_state.total_score == 10
        assert len(result.new_state.step_scores) == 1
        assert result.new_state.step_scores[0].score == 10
        assert result.new_state.step_scores[0].passed is True

    def test_lem_evaluation_determines_pass_fail(self):
        """Test that engine determines pass/fail based on threshold."""
        steps = [
            Mock(
                spec=ChallengeStep,
                step_index=0,
                step_type="CHAT",
                title="Question",
                instruction="Answer",
                points_possible=10,
                passing_threshold=70  # 70% = 7/10
            ),
            Mock(
                spec=ChallengeStep,
                step_index=1,
                step_type="MCQ_SINGLE",
                title="Next",
                instruction="Pick one"
            ),
        ]

        engine = GameEngine(steps)

        # Test passing score (8/10 = 80%)
        state = SessionState(
            session_id="test-session",
            challenge_id="test-challenge",
            user_id="test-user",
            current_step_index=0
        )

        event = Event(
            event_type=EventType.LEM_EVALUATED,
            session_id="test-session",
            sequence_number=4,
            timestamp=datetime.utcnow(),
            data={
                "raw_score": 8,
                "clamped_score": 8,
                "max_score": 10,
                "passed": True,
                "rationale": "Good answer",
                "tags": ["correct"],
                "step_index": 0
            }
        )

        result = engine.apply_event(state, event)

        # Should pass (8/10 = 80% > 70%)
        assert result.new_state.step_scores[0].passed is True
        # Should advance to next step
        assert result.new_state.current_step_index == 1


class TestUIResponseBuilder:
    """Test UI response building."""

    def test_ui_response_includes_required_fields(self):
        """Test that UI response includes all required fields."""
        steps = [
            Mock(
                spec=ChallengeStep,
                step_index=0,
                step_type="MCQ_SINGLE",
                title="Question 1",
                instruction="Pick the correct answer",
                options=["Option A", "Option B", "Option C"]
            ),
        ]

        engine = GameEngine(steps)

        state = SessionState(
            session_id="test-session",
            challenge_id="test-challenge",
            user_id="test-user",
            current_step_index=0,
            current_ui_mode="MCQ_SINGLE",
            total_score=0,
            max_possible_score=100,
            status="active"
        )

        event = Event(
            event_type=EventType.SESSION_STARTED,
            session_id="test-session",
            sequence_number=1,
            timestamp=datetime.utcnow(),
            data={}
        )

        result = engine.apply_event(state, event)

        ui_response = result.ui_response

        # Check required fields
        assert "ui_mode" in ui_response
        assert "step_index" in ui_response
        assert "total_steps" in ui_response
        assert "step_title" in ui_response
        assert "step_instruction" in ui_response
        assert "messages" in ui_response
        assert "score" in ui_response
        assert "max_score" in ui_response
        assert "status" in ui_response

        # Check values
        assert ui_response["ui_mode"] == "MCQ_SINGLE"
        assert ui_response["step_index"] == 0
        assert ui_response["total_steps"] == 1
        assert ui_response["options"] == ["Option A", "Option B", "Option C"]


class TestEngineResultStructure:
    """Test EngineResult structure."""

    def test_engine_result_has_required_fields(self):
        """Test that EngineResult has all required fields."""
        state = SessionState(
            session_id="test",
            challenge_id="challenge",
            user_id="user"
        )

        result = EngineResult(
            new_state=state,
            derived_events=[],
            llm_tasks=[],
            ui_response={"ui_mode": "CHAT"}
        )

        assert result.new_state == state
        assert isinstance(result.derived_events, list)
        assert isinstance(result.llm_tasks, list)
        assert isinstance(result.ui_response, dict)


class TestEngineDeterminism:
    """Test that engine is deterministic."""

    def test_same_event_produces_same_result(self):
        """Test that applying the same event twice produces same result."""
        steps = [
            Mock(
                spec=ChallengeStep,
                step_index=0,
                step_type="MCQ_SINGLE",
                title="Q1",
                instruction="Pick one",
                auto_narrate=False
            ),
        ]

        engine = GameEngine(steps)

        initial_state = SessionState(
            session_id="test-session",
            challenge_id="test-challenge",
            user_id="test-user"
        )

        event = Event(
            event_type=EventType.SESSION_STARTED,
            session_id="test-session",
            sequence_number=1,
            timestamp=datetime(2025, 1, 1, 12, 0, 0),  # Fixed timestamp
            data={}
        )

        # Apply event twice
        result1 = engine.apply_event(initial_state, event)
        result2 = engine.apply_event(initial_state, event)

        # Results should be identical
        assert result1.new_state.current_step_index == result2.new_state.current_step_index
        assert result1.new_state.status == result2.new_state.status
        assert result1.new_state.current_ui_mode == result2.new_state.current_ui_mode
        assert len(result1.derived_events) == len(result2.derived_events)
