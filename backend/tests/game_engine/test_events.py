"""
Unit tests for Event system.

Tests event creation, validation, and data schemas.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.game_engine.events import (
    Event,
    EventType,
    SessionCreatedData,
    SessionStartedData,
    UserSubmittedAnswerData,
    StepCompletedData,
    LEMEvaluatedData,
    GMNarratedData,
)


class TestEventCreation:
    """Test basic event creation and validation."""

    def test_create_session_started_event(self):
        """Test creating a SESSION_STARTED event."""
        event = Event(
            event_type=EventType.SESSION_STARTED,
            session_id="test-session-123",
            sequence_number=1,
            timestamp=datetime.utcnow(),
            data={"first_step_index": 0}
        )

        assert event.event_type == EventType.SESSION_STARTED
        assert event.session_id == "test-session-123"
        assert event.sequence_number == 1
        assert event.data["first_step_index"] == 0

    def test_create_user_submitted_answer_event(self):
        """Test creating a USER_SUBMITTED_ANSWER event."""
        event = Event(
            event_type=EventType.USER_SUBMITTED_ANSWER,
            session_id="test-session-123",
            sequence_number=2,
            timestamp=datetime.utcnow(),
            data={
                "step_index": 0,
                "answer": "This is my answer"
            }
        )

        assert event.event_type == EventType.USER_SUBMITTED_ANSWER
        assert event.data["step_index"] == 0
        assert event.data["answer"] == "This is my answer"

    def test_create_score_awarded_event(self):
        """Test creating a SCORE_AWARDED event."""
        event = Event(
            event_type=EventType.SCORE_AWARDED,
            session_id="test-session-123",
            sequence_number=3,
            timestamp=datetime.utcnow(),
            data={
                "step_index": 0,
                "points": 10,
                "reason": "Correct answer"
            }
        )

        assert event.event_type == EventType.SCORE_AWARDED
        assert event.data["points"] == 10

    def test_event_type_enum_values(self):
        """Test that all EventType enum values are valid."""
        # Session lifecycle
        assert EventType.SESSION_CREATED.value == "SESSION_CREATED"
        assert EventType.SESSION_STARTED.value == "SESSION_STARTED"
        assert EventType.SESSION_COMPLETED.value == "SESSION_COMPLETED"

        # User actions
        assert EventType.USER_SUBMITTED_ANSWER.value == "USER_SUBMITTED_ANSWER"
        assert EventType.USER_REQUESTED_HINT.value == "USER_REQUESTED_HINT"
        assert EventType.USER_CONTINUED.value == "USER_CONTINUED"

        # Engine-derived
        assert EventType.STEP_ENTERED.value == "STEP_ENTERED"
        assert EventType.STEP_COMPLETED.value == "STEP_COMPLETED"

        # LLM tasks
        assert EventType.LEM_EVALUATED.value == "LEM_EVALUATED"
        assert EventType.GM_NARRATED.value == "GM_NARRATED"


class TestEventDataSchemas:
    """Test event data schema validation."""

    def test_session_created_data_schema(self):
        """Test SessionCreatedData validation."""
        data = SessionCreatedData(
            challenge_id="challenge-123",
            user_id="user-456"
        )

        assert data.challenge_id == "challenge-123"
        assert data.user_id == "user-456"

    def test_user_submitted_answer_data_text(self):
        """Test UserSubmittedAnswerData with text answer."""
        data = UserSubmittedAnswerData(
            step_index=0,
            answer="My text answer"
        )

        assert data.step_index == 0
        assert data.answer == "My text answer"

    def test_user_submitted_answer_data_mcq_single(self):
        """Test UserSubmittedAnswerData with MCQ single answer."""
        data = UserSubmittedAnswerData(
            step_index=1,
            answer=2  # Index of selected option
        )

        assert data.step_index == 1
        assert data.answer == 2

    def test_user_submitted_answer_data_mcq_multi(self):
        """Test UserSubmittedAnswerData with MCQ multiple answers."""
        data = UserSubmittedAnswerData(
            step_index=2,
            answer=[0, 2, 3]  # Indices of selected options
        )

        assert data.step_index == 2
        assert data.answer == [0, 2, 3]

    def test_step_completed_data_schema(self):
        """Test StepCompletedData validation."""
        data = StepCompletedData(
            step_index=0,
            score_awarded=8,
            max_possible=10,
            passed=True
        )

        assert data.step_index == 0
        assert data.score_awarded == 8
        assert data.max_possible == 10
        assert data.passed is True

    def test_lem_evaluated_data_schema(self):
        """Test LEMEvaluatedData validation."""
        data = LEMEvaluatedData(
            step_index=1,
            raw_score=12,  # LEM gave 12
            clamped_score=10,  # Engine clamped to max
            max_score=10,
            passed=True,
            rationale="Answer demonstrates good understanding",
            tags=["correct", "detailed"]
        )

        assert data.raw_score == 12
        assert data.clamped_score == 10
        assert data.passed is True
        assert len(data.tags) == 2

    def test_gm_narrated_data_schema(self):
        """Test GMNarratedData validation."""
        data = GMNarratedData(
            step_index=0,
            content="Welcome to the challenge!",
            task_type="introduction"
        )

        assert data.step_index == 0
        assert "Welcome" in data.content
        assert data.task_type == "introduction"


class TestEventSequencing:
    """Test event sequencing and ordering."""

    def test_events_have_sequence_numbers(self):
        """Test that events maintain sequence order."""
        events = [
            Event(
                event_type=EventType.SESSION_CREATED,
                session_id="test",
                sequence_number=0,
                timestamp=datetime.utcnow(),
                data={}
            ),
            Event(
                event_type=EventType.SESSION_STARTED,
                session_id="test",
                sequence_number=1,
                timestamp=datetime.utcnow(),
                data={}
            ),
            Event(
                event_type=EventType.STEP_ENTERED,
                session_id="test",
                sequence_number=2,
                timestamp=datetime.utcnow(),
                data={}
            ),
        ]

        # Verify sequence numbers are in order
        for i, event in enumerate(events):
            assert event.sequence_number == i

    def test_events_same_session(self):
        """Test that events can be grouped by session_id."""
        session_id = "test-session-789"

        events = [
            Event(
                event_type=EventType.SESSION_STARTED,
                session_id=session_id,
                sequence_number=1,
                timestamp=datetime.utcnow(),
                data={}
            ),
            Event(
                event_type=EventType.USER_SUBMITTED_ANSWER,
                session_id=session_id,
                sequence_number=2,
                timestamp=datetime.utcnow(),
                data={}
            ),
        ]

        # All events should have same session_id
        assert all(e.session_id == session_id for e in events)


class TestEventImmutability:
    """Test event immutability patterns."""

    def test_event_to_dict(self):
        """Test that events can be serialized to dict."""
        event = Event(
            event_type=EventType.SESSION_STARTED,
            session_id="test",
            sequence_number=1,
            timestamp=datetime.utcnow(),
            data={"test": "value"}
        )

        event_dict = event.model_dump()

        assert event_dict["event_type"] == "SESSION_STARTED"
        assert event_dict["session_id"] == "test"
        assert event_dict["data"]["test"] == "value"

    def test_event_from_dict(self):
        """Test that events can be deserialized from dict."""
        timestamp = datetime.utcnow()
        event_dict = {
            "event_type": "SESSION_STARTED",
            "session_id": "test",
            "sequence_number": 1,
            "timestamp": timestamp,
            "data": {"test": "value"}
        }

        event = Event(**event_dict)

        assert event.event_type == EventType.SESSION_STARTED
        assert event.session_id == "test"
        assert event.data["test"] == "value"
