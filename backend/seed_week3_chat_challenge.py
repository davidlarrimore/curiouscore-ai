"""
Seed Week 3 Test Challenge with CHAT Step

Creates a simple challenge with:
1. MCQ_SINGLE step (warmup)
2. CHAT step with LEM evaluation (rubric-based)
3. MCQ_SINGLE step (validation)

This validates the complete LEM integration:
- User submits free-text answer
- LEM evaluates against rubric
- Engine enforces score clamping and thresholds
- Session advances on passing score
"""

import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.database import Base
from app.models import Challenge, ChallengeStep, User
from app.config import settings


async def seed_week3_challenge():
    """Create Week 3 test challenge with CHAT step."""
    # Create async engine
    engine = create_async_engine(settings.database_url, echo=True)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Ensure test user exists
        result = await session.execute(
            select(User).where(User.id == "test-user-id")
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                id="test-user-id",
                email="test@example.com",
                username="testuser",
                hashed_password="fake-hash",
                role="user"
            )
            session.add(user)
            await session.commit()
            print(f"✅ Created test user: {user.id}")

        # Delete existing Week 3 challenge if exists
        result = await session.execute(
            select(Challenge).where(Challenge.title.like("Week 3 Test Challenge%"))
        )
        existing = result.scalar_one_or_none()
        if existing:
            # Delete steps first
            result = await session.execute(
                select(ChallengeStep).where(ChallengeStep.challenge_id == existing.id)
            )
            steps = result.scalars().all()
            for step in steps:
                await session.delete(step)
            await session.delete(existing)
            await session.commit()
            print("✅ Deleted existing Week 3 challenge")

        # Create new challenge
        challenge_id = str(uuid.uuid4())
        challenge = Challenge(
            id=challenge_id,
            title="Week 3 Test Challenge: CHAT with LEM",
            description="Test challenge with CHAT step for LEM evaluation",
            tags=["test", "week3", "lem"],
            difficulty="beginner",
            system_prompt="Test challenge for LEM evaluation",
            estimated_time_minutes=10,
            xp_reward=50,
            passing_score=60,
            is_active=True
        )
        session.add(challenge)
        await session.commit()
        print(f"✅ Created challenge: {challenge.id}")

        # Step 1: MCQ_SINGLE (warmup)
        step1 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=0,
            step_type="MCQ_SINGLE",
            title="What is a function?",
            instruction="Select the best definition of a function in programming.",
            options=[
                "A reusable block of code that performs a specific task",  # Correct
                "A variable that stores data",
                "A type of loop",
                "A comment in the code"
            ],
            correct_answer=0,
            points_possible=20,
            passing_threshold=100,
            auto_narrate=False
        )
        session.add(step1)

        # Step 2: CHAT with LEM evaluation
        rubric = {
            "total_points": 50,
            "criteria": {
                "reusability": {
                    "description": "Explains that functions allow code reuse",
                    "points": 20
                },
                "organization": {
                    "description": "Mentions that functions help organize code",
                    "points": 15
                },
                "examples": {
                    "description": "Provides at least one concrete example",
                    "points": 15
                }
            },
            "passing_threshold": 60  # Need 30/50 points to pass
        }

        step2 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=1,
            step_type="CHAT",
            title="Explain why we use functions",
            instruction="In your own words, explain why programmers use functions in their code. Provide at least one specific benefit and an example.",
            rubric=rubric,
            points_possible=50,
            passing_threshold=60,
            auto_narrate=True,
            gm_context="This is a fundamental programming concept. Encourage the learner to think about real-world code organization."
        )
        session.add(step2)

        # Step 3: MCQ_SINGLE (validation)
        step3 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=2,
            step_type="MCQ_SINGLE",
            title="Function best practice",
            instruction="Which is a best practice when writing functions?",
            options=[
                "Functions should be large and do many things",
                "Each function should have a single, clear purpose",  # Correct
                "Functions should never return values",
                "Functions should only be used for calculations"
            ],
            correct_answer=1,
            points_possible=30,
            passing_threshold=100,
            auto_narrate=False
        )
        session.add(step3)

        await session.commit()

        print(f"""
✅ Week 3 Challenge Created Successfully!

Challenge ID: {challenge.id}
Steps:
  0. MCQ_SINGLE: What is a function? (20 points)
  1. CHAT: Explain why we use functions (50 points, LEM evaluation)
  2. MCQ_SINGLE: Function best practice (30 points)

Total: 100 points
Passing: 60%

Test Flow:
1. Answer warmup MCQ
2. Submit free-text answer → LEM evaluates against rubric
3. Engine enforces score clamping and threshold
4. Complete final MCQ

Run: pytest backend/tests/test_week3_chat_lem.py -v -s
""")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_week3_challenge())
