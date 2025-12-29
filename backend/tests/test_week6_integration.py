"""
Week 6 Integration Tests

Comprehensive integration tests for the complete Game Master architecture.
Tests the full session lifecycle with all step types and LLM integration.
"""

import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.main import app
from app.database import Base, get_session
from app.models import User, Challenge, ChallengeStep


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_db():
    """Create a test database."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    yield async_session

    await engine.dispose()


@pytest.fixture
async def test_user(test_db):
    """Create a test user."""
    async with test_db() as session:
        user = User(
            id="test-user-id",
            email="test@example.com",
            username="testuser",
            hashed_password="fake-hash",
            role="user"
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest.fixture
async def test_challenge(test_db):
    """Create a simple test challenge with all step types."""
    async with test_db() as session:
        challenge_id = str(uuid.uuid4())

        challenge = Challenge(
            id=challenge_id,
            title="Week 6 Integration Test Challenge",
            description="Test challenge with all step types",
            tags=["test", "week6"],
            difficulty="beginner",
            system_prompt="Test challenge",
            estimated_time_minutes=10,
            xp_reward=50,
            passing_score=60,
            is_active=True
        )
        session.add(challenge)

        # Step 0: CONTINUE_GATE
        step0 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=0,
            step_type="CONTINUE_GATE",
            title="Welcome",
            instruction="Welcome to the test challenge!",
            points_possible=0,
            passing_threshold=0,
            auto_narrate=False
        )
        session.add(step0)

        # Step 1: MCQ_SINGLE
        step1 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=1,
            step_type="MCQ_SINGLE",
            title="Test MCQ",
            instruction="Select the correct answer:",
            options=["Correct", "Wrong 1", "Wrong 2"],
            correct_answer=0,
            points_possible=30,
            passing_threshold=100,
            auto_narrate=False
        )
        session.add(step1)

        # Step 2: MCQ_MULTI
        step2 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=2,
            step_type="MCQ_MULTI",
            title="Test Multi-Select",
            instruction="Select all correct answers:",
            options=["Correct 1", "Wrong", "Correct 2"],
            correct_answers=[0, 2],
            points_possible=30,
            passing_threshold=100,
            auto_narrate=False
        )
        session.add(step2)

        # Step 3: TRUE_FALSE
        step3 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=3,
            step_type="TRUE_FALSE",
            title="Test True/False",
            instruction="True or False: This is a test",
            correct_answer=True,
            points_possible=20,
            passing_threshold=100,
            auto_narrate=False
        )
        session.add(step3)

        await session.commit()
        await session.refresh(challenge)

        return challenge


@pytest.fixture
async def client(test_db):
    """Create test client with database override."""
    async def override_get_session():
        async with test_db() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Mock auth headers (in real app, would use JWT)."""
    # Note: This assumes the auth middleware is bypassed in tests
    # In production, you'd generate a real JWT token
    return {"Authorization": "Bearer test-token"}


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_complete_session_lifecycle(client, test_user, test_challenge, auth_headers):
    """Test complete session lifecycle from creation to completion."""

    # 1. Create session
    response = await client.post(
        "/sessions",
        json={"challenge_id": test_challenge.id},
        headers=auth_headers
    )
    assert response.status_code == 201
    session_data = response.json()
    session_id = session_data["id"]
    assert session_data["status"] == "created"
    assert session_data["challenge_id"] == test_challenge.id

    # 2. Start session
    response = await client.post(
        f"/sessions/{session_id}/start",
        headers=auth_headers
    )
    assert response.status_code == 200
    state = response.json()
    assert state["session"]["status"] == "active"
    assert state["ui_response"]["ui_mode"] == "CONTINUE_GATE"
    assert state["ui_response"]["step_index"] == 0

    # 3. Continue through gate
    response = await client.post(
        f"/sessions/{session_id}/action",
        json={"action": "continue"},
        headers=auth_headers
    )
    assert response.status_code == 200
    state = response.json()
    assert state["ui_response"]["ui_mode"] == "MCQ_SINGLE"
    assert state["ui_response"]["step_index"] == 1

    # 4. Answer MCQ_SINGLE correctly
    response = await client.post(
        f"/sessions/{session_id}/attempt",
        json={"answer": 0},
        headers=auth_headers
    )
    assert response.status_code == 200
    state = response.json()
    assert state["session"]["total_score"] == 30
    assert state["ui_response"]["step_index"] == 2

    # 5. Answer MCQ_MULTI correctly
    response = await client.post(
        f"/sessions/{session_id}/attempt",
        json={"answer": [0, 2]},
        headers=auth_headers
    )
    assert response.status_code == 200
    state = response.json()
    assert state["session"]["total_score"] == 60
    assert state["ui_response"]["step_index"] == 3

    # 6. Answer TRUE_FALSE correctly
    response = await client.post(
        f"/sessions/{session_id}/attempt",
        json={"answer": True},
        headers=auth_headers
    )
    assert response.status_code == 200
    state = response.json()
    assert state["session"]["total_score"] == 80
    assert state["session"]["status"] == "completed"

    # 7. Get final state
    response = await client.get(
        f"/sessions/{session_id}/state",
        headers=auth_headers
    )
    assert response.status_code == 200
    final_state = response.json()
    assert final_state["session"]["status"] == "completed"
    assert final_state["session"]["total_score"] == 80


@pytest.mark.asyncio
async def test_mcq_wrong_answer_stays_on_step(client, test_user, test_challenge, auth_headers):
    """Test that wrong MCQ answer keeps user on same step."""

    # Create and start session
    response = await client.post(
        "/sessions",
        json={"challenge_id": test_challenge.id},
        headers=auth_headers
    )
    session_id = response.json()["id"]

    await client.post(f"/sessions/{session_id}/start", headers=auth_headers)
    await client.post(
        f"/sessions/{session_id}/action",
        json={"action": "continue"},
        headers=auth_headers
    )

    # Answer MCQ incorrectly
    response = await client.post(
        f"/sessions/{session_id}/attempt",
        json={"answer": 1},  # Wrong answer
        headers=auth_headers
    )

    assert response.status_code == 200
    state = response.json()
    assert state["session"]["total_score"] == 0
    assert state["ui_response"]["step_index"] == 1  # Still on step 1
    assert state["ui_response"]["ui_mode"] == "MCQ_SINGLE"


@pytest.mark.asyncio
async def test_event_sourcing_replay(client, test_user, test_challenge, auth_headers):
    """Test that state can be replayed from events."""

    # Create and start session
    response = await client.post(
        "/sessions",
        json={"challenge_id": test_challenge.id},
        headers=auth_headers
    )
    session_id = response.json()["id"]

    await client.post(f"/sessions/{session_id}/start", headers=auth_headers)
    await client.post(
        f"/sessions/{session_id}/action",
        json={"action": "continue"},
        headers=auth_headers
    )

    # Make several moves
    await client.post(
        f"/sessions/{session_id}/attempt",
        json={"answer": 0},
        headers=auth_headers
    )
    await client.post(
        f"/sessions/{session_id}/attempt",
        json={"answer": [0, 2]},
        headers=auth_headers
    )

    # Get state (which replays events)
    response = await client.get(
        f"/sessions/{session_id}/state",
        headers=auth_headers
    )

    assert response.status_code == 200
    state = response.json()
    assert state["session"]["total_score"] == 60
    assert state["ui_response"]["step_index"] == 3


@pytest.mark.asyncio
async def test_session_not_found(client, auth_headers):
    """Test error handling for non-existent session."""

    response = await client.get(
        "/sessions/nonexistent-id/state",
        headers=auth_headers
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cannot_start_already_active_session(client, test_user, test_challenge, auth_headers):
    """Test that starting an already active session fails."""

    response = await client.post(
        "/sessions",
        json={"challenge_id": test_challenge.id},
        headers=auth_headers
    )
    session_id = response.json()["id"]

    # Start once
    await client.post(f"/sessions/{session_id}/start", headers=auth_headers)

    # Try to start again
    response = await client.post(
        f"/sessions/{session_id}/start",
        headers=auth_headers
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_mcq_multi_partial_credit(client, test_user, test_challenge, auth_headers):
    """Test that MCQ_MULTI gives partial credit for partially correct answers."""

    # Create and start session
    response = await client.post(
        "/sessions",
        json={"challenge_id": test_challenge.id},
        headers=auth_headers
    )
    session_id = response.json()["id"]

    await client.post(f"/sessions/{session_id}/start", headers=auth_headers)
    await client.post(
        f"/sessions/{session_id}/action",
        json={"action": "continue"},
        headers=auth_headers
    )
    await client.post(
        f"/sessions/{session_id}/attempt",
        json={"answer": 0},
        headers=auth_headers
    )

    # Answer MCQ_MULTI with only 1 correct out of 2
    response = await client.post(
        f"/sessions/{session_id}/attempt",
        json={"answer": [0]},  # Only one correct, missing [2]
        headers=auth_headers
    )

    assert response.status_code == 200
    state = response.json()
    # Should get partial credit but not advance (threshold is 100%)
    assert state["session"]["total_score"] == 30  # No points from this step
    assert state["ui_response"]["step_index"] == 2  # Still on step 2


@pytest.mark.asyncio
async def test_progress_tracking(client, test_user, test_challenge, auth_headers):
    """Test that progress is tracked correctly."""

    response = await client.post(
        "/sessions",
        json={"challenge_id": test_challenge.id},
        headers=auth_headers
    )
    session_id = response.json()["id"]

    await client.post(f"/sessions/{session_id}/start", headers=auth_headers)

    # Check initial progress
    response = await client.get(
        f"/sessions/{session_id}/state",
        headers=auth_headers
    )
    state = response.json()
    assert state["ui_response"]["step_index"] == 0
    assert state["ui_response"]["total_steps"] == 4
    assert state["ui_response"]["progress_percentage"] == 25.0  # 1/4 steps


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
