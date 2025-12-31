"""
Seed Week 4 Test Challenge with CONTINUE_GATE Steps

Creates a narrative-driven challenge with:
1. CONTINUE_GATE step (welcome)
2. CHAT step with hint support
3. CONTINUE_GATE step (transition)
4. MCQ_SINGLE step (validation)
5. CONTINUE_GATE step (conclusion)

This validates the complete Week 4 implementation:
- Continue gates for narrative pacing
- Hint requests with TEACH_HINTS LLM task
- Smooth UX with loading states
"""

import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.database import Base
from app.models import Challenge, ChallengeStep, User
from app.config import settings


async def seed_week4_challenge():
    """Create Week 4 test challenge with CONTINUE_GATE steps."""
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

        # Delete existing Week 4 challenge if exists
        result = await session.execute(
            select(Challenge).where(Challenge.title.like("Week 4 Test Challenge%"))
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
            print("✅ Deleted existing Week 4 challenge")

        # Create new challenge
        challenge_id = str(uuid.uuid4())
        challenge = Challenge(
            id=challenge_id,
            title="Week 4 Test Challenge: Narrative Gates & Hints",
            description="Test challenge with CONTINUE_GATE steps and hint functionality",
            tags=["test", "week4", "gates", "hints"],
            difficulty="beginner",
            challenge_type="advanced",  # Multi-step challenge with CONTINUE_GATE, CHAT, MCQ_SINGLE
            system_prompt="Narrative-driven challenge for testing continue gates and hints",
            estimated_time_minutes=15,
            xp_reward=75,
            passing_score=60,
            is_active=True
        )
        session.add(challenge)
        await session.commit()
        print(f"✅ Created challenge: {challenge.id}")

        # Step 0: CONTINUE_GATE (welcome)
        step0 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=0,
            step_type="CONTINUE_GATE",
            title="Welcome to Variables",
            instruction="Welcome! In this challenge, you'll learn about variables in programming. Variables are like labeled containers that store information your program can use and change. When you're ready to begin, click Continue.",
            points_possible=0,
            passing_threshold=0,
            auto_narrate=True,
            gm_context="This is an introduction to variables. Set an encouraging, supportive tone."
        )
        session.add(step0)

        # Step 1: CHAT with hint support
        rubric = {
            "total_points": 40,
            "criteria": {
                "storage": {
                    "description": "Explains that variables store data/values",
                    "points": 15
                },
                "naming": {
                    "description": "Mentions that variables have names/labels",
                    "points": 10
                },
                "purpose": {
                    "description": "Describes why variables are useful (reusability, tracking)",
                    "points": 15
                }
            },
            "passing_threshold": 60  # Need 24/40 points to pass
        }

        step1 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=1,
            step_type="CHAT",
            title="What are variables?",
            instruction="In your own words, explain what a variable is in programming and why programmers use them. If you need help, you can request a hint!",
            rubric=rubric,
            points_possible=40,
            passing_threshold=60,
            auto_narrate=True,
            gm_context="The learner is explaining variables. Focus on the concept of storage, naming, and reusability. Be encouraging and supportive."
        )
        session.add(step1)

        # Step 2: CONTINUE_GATE (transition)
        step2 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=2,
            step_type="CONTINUE_GATE",
            title="Variable Types",
            instruction="Great work! Now let's explore different types of data that variables can store. In most programming languages, variables can hold numbers, text (strings), boolean values (true/false), and more. Ready to continue?",
            points_possible=0,
            passing_threshold=0,
            auto_narrate=False
        )
        session.add(step2)

        # Step 3: MCQ_SINGLE (validation)
        step3 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=3,
            step_type="MCQ_SINGLE",
            title="Variable naming",
            instruction="Which of the following is a good variable name for storing a user's age?",
            options=[
                "age",  # Correct
                "a",
                "123age",
                "user-age"
            ],
            correct_answer=0,
            points_possible=30,
            passing_threshold=100,
            auto_narrate=False
        )
        session.add(step3)

        # Step 4: CONTINUE_GATE (conclusion)
        step4 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=4,
            step_type="CONTINUE_GATE",
            title="Conclusion",
            instruction="Excellent! You've completed the Variables challenge. You've learned what variables are, why they're useful, and how to name them effectively. Variables are fundamental building blocks in programming - you'll use them in every program you write!",
            points_possible=0,
            passing_threshold=0,
            auto_narrate=True,
            gm_context="Celebrate the learner's completion. Emphasize how important variables are to all programming."
        )
        session.add(step4)

        await session.commit()

        print(f"""
✅ Week 4 Challenge Created Successfully!

Challenge ID: {challenge.id}
Steps:
  0. CONTINUE_GATE: Welcome to Variables (0 points, GM narration)
  1. CHAT: What are variables? (40 points, hint support, LEM evaluation)
  2. CONTINUE_GATE: Variable Types (0 points, transition)
  3. MCQ_SINGLE: Variable naming (30 points)
  4. CONTINUE_GATE: Conclusion (0 points, GM narration)

Total: 70 points
Passing: 60%

Test Flow:
1. Click Continue on welcome gate
2. Submit free-text answer (can request hint if needed) → LEM evaluates
3. Click Continue on transition gate
4. Answer MCQ about variable naming
5. Click Continue on conclusion gate → Challenge complete!

Features Validated:
- ✅ CONTINUE_GATE steps with narrative pacing
- ✅ Hint requests with TEACH_HINTS LLM task
- ✅ GM narration on gates (steps 0 and 4)
- ✅ Smooth UX with loading states
""")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_week4_challenge())
