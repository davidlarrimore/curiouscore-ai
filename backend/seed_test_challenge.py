"""
Seed script for Week 2 testing: Creates a simple 3-step MCQ challenge.

Usage:
    cd backend
    source ../.venv/bin/activate
    python seed_test_challenge.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import Base, Challenge, ChallengeStep, User
from app.config import settings
import uuid
from datetime import datetime

async def seed_test_challenge():
    """Create a minimal 3-step MCQ challenge for Week 2 testing."""

    # Create async engine
    engine = create_async_engine(
        settings.database_url,
        echo=True,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Check if test user exists, create if not
        test_user = await session.get(User, "test-user-id")
        if not test_user:
            test_user = User(
                id="test-user-id",
                email="test@example.com",
                hashed_password="$2b$12$dummy",  # Dummy hash
                username="Test User",
                role="user",
                xp=0,
                level=1
            )
            session.add(test_user)

        # Create test challenge
        challenge_id = str(uuid.uuid4())
        challenge = Challenge(
            id=challenge_id,
            title="Week 2 Test Challenge: Python Basics",
            description="A simple 3-step MCQ challenge to validate Week 2 implementation",
            difficulty="beginner",
            xp_reward=100,
            is_active=True,
            tags=["python", "basics", "test"],
            system_prompt="Test challenge for Game Master MVP"
        )
        session.add(challenge)

        # Step 1: MCQ_SINGLE
        step1 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=0,
            step_type="MCQ_SINGLE",
            title="What is a variable?",
            instruction="Select the best definition of a variable in programming.",
            options=[
                "A container for storing data values",
                "A type of loop",
                "A function that returns nothing",
                "A mathematical operator"
            ],
            correct_answer=0,  # First option is correct
            points_possible=30,
            passing_threshold=100,  # Must get it right
            gm_context="Introduce the concept of variables in a friendly way."
        )
        session.add(step1)

        # Step 2: MCQ_MULTI
        step2 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=1,
            step_type="MCQ_MULTI",
            title="Data Types",
            instruction="Select all valid Python data types. (Select multiple answers)",
            options=[
                "int",
                "string",
                "array",
                "list",
                "bool"
            ],
            correct_answers=[0, 3, 4],  # int, list, bool are correct
            points_possible=40,
            passing_threshold=75,  # Need at least 75% correct
            gm_context="Test knowledge of Python's built-in types."
        )
        session.add(step2)

        # Step 3: TRUE_FALSE
        step3 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=2,
            step_type="TRUE_FALSE",
            title="Lists are Mutable",
            instruction="True or False: In Python, lists can be modified after creation (they are mutable).",
            correct_answer=0,  # 0 = True
            points_possible=30,
            passing_threshold=100,  # Must get it right
            gm_context="Wrap up with a fundamental concept about Python lists."
        )
        session.add(step3)

        await session.commit()

        print(f"✅ Successfully created test challenge: {challenge_id}")
        print(f"   - Title: {challenge.title}")
        print(f"   - Steps: 3 (MCQ_SINGLE, MCQ_MULTI, TRUE_FALSE)")
        print(f"   - Total Points: 100")
        print(f"\n📝 To test:")
        print(f"   1. Start the backend: uvicorn app.main:app --reload --port 8000")
        print(f"   2. Start the frontend: npm run dev")
        print(f"   3. Navigate to: http://localhost:8080/challenge/{challenge_id}")
        print(f"   4. Complete all 3 steps and verify scoring")

    await engine.dispose()

if __name__ == "__main__":
    print("🌱 Seeding test challenge for Week 2 validation...\n")
    asyncio.run(seed_test_challenge())
