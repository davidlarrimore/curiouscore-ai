"""
Unit tests for SessionState.

Tests state initialization, mutation, and helper methods.
"""

import pytest
from datetime import datetime

from app.game_engine.state import SessionState, StepScore, DisplayMessage


class TestSessionStateInitialization:
    """Test SessionState initialization."""

    def test_create_initial_state(self):
        """Test creating a fresh SessionState."""
        state = SessionState(
            session_id="test-session-123",
            challenge_id="challenge-456",
            user_id="user-789"
        )

        assert state.session_id == "test-session-123"
        assert state.challenge_id == "challenge-456"
        assert state.user_id == "user-789"
        assert state.current_step_index == 0
        assert state.status == "active"
        assert state.total_score == 0
        assert state.max_possible_score == 100
        assert len(state.messages) == 0
        assert len(state.step_scores) == 0

    def test_state_with_custom_values(self):
        """Test creating state with custom initial values."""
        state = SessionState(
            session_id="test",
            challenge_id="challenge",
            user_id="user",
            current_step_index=2,
            total_score=50,
            max_possible_score=200,
            status="completed"
        )

        assert state.current_step_index == 2
        assert state.total_score == 50
        assert state.max_possible_score == 200
        assert state.status == "completed"


class TestStepScore:
    """Test StepScore model."""

    def test_create_step_score(self):
        """Test creating a StepScore."""
        score = StepScore(
            step_index=0,
            score=8,
            max_possible=10,
            passed=True,
            attempts=1
        )

        assert score.step_index == 0
        assert score.score == 8
        assert score.max_possible == 10
        assert score.passed is True
        assert score.attempts == 1

    def test_step_score_failed(self):
        """Test creating a failed StepScore."""
        score = StepScore(
            step_index=1,
            score=3,
            max_possible=10,
            passed=False,
            attempts=2
        )

        assert score.passed is False
        assert score.attempts == 2


class TestDisplayMessage:
    """Test DisplayMessage model."""

    def test_create_user_message(self):
        """Test creating a user message."""
        msg = DisplayMessage(
            role="user",
            content="This is my answer",
            timestamp=datetime.utcnow().isoformat()
        )

        assert msg.role == "user"
        assert msg.content == "This is my answer"
        assert msg.metadata is None

    def test_create_gm_message_with_metadata(self):
        """Test creating a GM message with metadata."""
        msg = DisplayMessage(
            role="gm",
            content="Great job! You earned 10 points.",
            timestamp=datetime.utcnow().isoformat(),
            metadata={"score": 10, "max": 10}
        )

        assert msg.role == "gm"
        assert msg.metadata["score"] == 10


class TestSessionStateMethods:
    """Test SessionState helper methods."""

    def test_calculate_final_percentage(self):
        """Test percentage calculation."""
        state = SessionState(
            session_id="test",
            challenge_id="challenge",
            user_id="user",
            total_score=75,
            max_possible_score=100
        )

        assert state.calculate_final_percentage() == 75.0

    def test_calculate_final_percentage_zero_max(self):
        """Test percentage calculation with zero max score."""
        state = SessionState(
            session_id="test",
            challenge_id="challenge",
            user_id="user",
            total_score=0,
            max_possible_score=0
        )

        assert state.calculate_final_percentage() == 0.0

    def test_add_message(self):
        """Test adding a message to state."""
        state = SessionState(
            session_id="test",
            challenge_id="challenge",
            user_id="user"
        )

        timestamp = datetime.utcnow().isoformat()
        state.add_message("user", "Hello", timestamp)

        assert len(state.messages) == 1
        assert state.messages[0].role == "user"
        assert state.messages[0].content == "Hello"

    def test_add_multiple_messages(self):
        """Test adding multiple messages."""
        state = SessionState(
            session_id="test",
            challenge_id="challenge",
            user_id="user"
        )

        timestamp = datetime.utcnow().isoformat()
        state.add_message("user", "Question 1", timestamp)
        state.add_message("gm", "Answer 1", timestamp)
        state.add_message("user", "Question 2", timestamp)

        assert len(state.messages) == 3
        assert state.messages[0].role == "user"
        assert state.messages[1].role == "gm"
        assert state.messages[2].role == "user"

    def test_add_message_with_metadata(self):
        """Test adding message with metadata."""
        state = SessionState(
            session_id="test",
            challenge_id="challenge",
            user_id="user"
        )

        timestamp = datetime.utcnow().isoformat()
        state.add_message("gm", "Score: 10/10", timestamp, metadata={"score": 10})

        assert len(state.messages) == 1
        assert state.messages[0].metadata["score"] == 10

    def test_is_step_passed(self):
        """Test checking if a step was passed."""
        state = SessionState(
            session_id="test",
            challenge_id="challenge",
            user_id="user",
            step_scores=[
                StepScore(step_index=0, score=8, max_possible=10, passed=True),
                StepScore(step_index=1, score=5, max_possible=10, passed=False),
            ]
        )

        assert state.is_step_passed(0) is True
        assert state.is_step_passed(1) is False
        assert state.is_step_passed(2) is False  # Not attempted

    def test_get_step_score(self):
        """Test getting score for a specific step."""
        state = SessionState(
            session_id="test",
            challenge_id="challenge",
            user_id="user",
            step_scores=[
                StepScore(step_index=0, score=8, max_possible=10, passed=True),
                StepScore(step_index=1, score=5, max_possible=10, passed=False),
            ]
        )

        score_0 = state.get_step_score(0)
        assert score_0 is not None
        assert score_0.score == 8

        score_1 = state.get_step_score(1)
        assert score_1 is not None
        assert score_1.score == 5

        score_2 = state.get_step_score(2)
        assert score_2 is None  # Not attempted

    def test_update_context_summary(self):
        """Test updating context summary."""
        state = SessionState(
            session_id="test",
            challenge_id="challenge",
            user_id="user"
        )

        state.update_context_summary("User has completed 2 steps with good scores.")

        assert state.context_summary == "User has completed 2 steps with good scores."

    def test_update_context_summary_truncates_long_text(self):
        """Test that context summary is truncated if too long."""
        state = SessionState(
            session_id="test",
            challenge_id="challenge",
            user_id="user"
        )

        # Create a very long summary (> 2000 chars)
        long_summary = "x" * 3000

        state.update_context_summary(long_summary)

        # Should be truncated to 2000 chars
        assert len(state.context_summary) == 2000


class TestSessionStateCopyOnWrite:
    """Test state immutability via copy-on-write."""

    def test_model_copy_creates_independent_copy(self):
        """Test that model_copy creates independent state."""
        original = SessionState(
            session_id="test",
            challenge_id="challenge",
            user_id="user",
            total_score=50
        )

        # Deep copy
        copy = original.model_copy(deep=True)

        # Modify copy
        copy.total_score = 100

        # Original should be unchanged
        assert original.total_score == 50
        assert copy.total_score == 100

    def test_messages_list_is_independent_after_copy(self):
        """Test that messages list is independent after copy."""
        original = SessionState(
            session_id="test",
            challenge_id="challenge",
            user_id="user"
        )

        original.add_message("user", "Original message", datetime.utcnow().isoformat())

        # Deep copy
        copy = original.model_copy(deep=True)

        # Add to copy
        copy.add_message("user", "Copy message", datetime.utcnow().isoformat())

        # Original should have only 1 message
        assert len(original.messages) == 1
        assert len(copy.messages) == 2


class TestSessionStateSerialization:
    """Test state serialization for snapshots."""

    def test_state_to_dict(self):
        """Test serializing state to dict."""
        state = SessionState(
            session_id="test-123",
            challenge_id="challenge-456",
            user_id="user-789",
            total_score=75,
            step_scores=[
                StepScore(step_index=0, score=25, max_possible=25, passed=True)
            ]
        )

        state_dict = state.model_dump()

        assert state_dict["session_id"] == "test-123"
        assert state_dict["total_score"] == 75
        assert len(state_dict["step_scores"]) == 1
        assert state_dict["step_scores"][0]["score"] == 25

    def test_state_from_dict(self):
        """Test deserializing state from dict."""
        state_dict = {
            "session_id": "test-123",
            "challenge_id": "challenge-456",
            "user_id": "user-789",
            "current_step_index": 2,
            "status": "active",
            "step_scores": [
                {"step_index": 0, "score": 25, "max_possible": 25, "passed": True, "attempts": 1}
            ],
            "total_score": 25,
            "max_possible_score": 100,
            "messages": [],
            "current_ui_mode": "CHAT",
            "current_ui_data": None,
            "mistakes_count": 0,
            "hints_used": 0,
            "context_summary": "",
            "flags": {}
        }

        state = SessionState(**state_dict)

        assert state.session_id == "test-123"
        assert state.current_step_index == 2
        assert len(state.step_scores) == 1
        assert state.step_scores[0].score == 25
