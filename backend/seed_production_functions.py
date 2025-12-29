"""
Production Challenge: Introduction to Functions

A comprehensive beginner-level challenge teaching function fundamentals
through a mix of MCQ, CHAT, and CONTINUE_GATE steps.

Total: 100 points | Passing: 70%
"""

import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.database import Base
from app.models import Challenge, ChallengeStep, User
from app.config import settings


async def seed_functions_challenge():
    """Create 'Introduction to Functions' production challenge."""
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

        # Delete existing challenge if exists
        result = await session.execute(
            select(Challenge).where(Challenge.title == "Introduction to Functions")
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
            print("✅ Deleted existing 'Introduction to Functions' challenge")

        # Create challenge
        challenge_id = str(uuid.uuid4())
        challenge = Challenge(
            id=challenge_id,
            title="Introduction to Functions",
            description="Master the fundamentals of functions in programming. Learn what functions are, why they're essential, and how to use them effectively.",
            tags=["beginner", "functions", "programming-basics"],
            difficulty="beginner",
            system_prompt="Teaching fundamental concepts of functions in programming",
            estimated_time_minutes=20,
            xp_reward=100,
            passing_score=70,
            is_active=True
        )
        session.add(challenge)
        await session.commit()
        print(f"✅ Created challenge: {challenge.id}")

        # Step 0: CONTINUE_GATE - Welcome
        step0 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=0,
            step_type="CONTINUE_GATE",
            title="Welcome to Functions",
            instruction="Welcome! In this challenge, you'll explore one of the most important concepts in programming: functions. Functions are reusable blocks of code that perform specific tasks. They're the building blocks that help us write organized, efficient programs. Ready to dive in?",
            points_possible=0,
            passing_threshold=0,
            auto_narrate=True,
            gm_context="This is an introduction to functions for beginners. Set an encouraging, supportive tone. Emphasize that functions are fundamental and learnable."
        )
        session.add(step0)

        # Step 1: MCQ_SINGLE - What is a function?
        step1 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=1,
            step_type="MCQ_SINGLE",
            title="What is a function?",
            instruction="Let's start with the basics. Which of the following best defines a function in programming?",
            options=[
                "A reusable block of code that performs a specific task",  # Correct
                "A variable that stores data",
                "A type of loop that repeats code",
                "A comment that explains code"
            ],
            correct_answer=0,
            points_possible=20,
            passing_threshold=100,
            auto_narrate=False
        )
        session.add(step1)

        # Step 2: CHAT - Why use functions?
        rubric_step2 = {
            "total_points": 30,
            "criteria": {
                "reusability": {
                    "description": "Explains that functions allow code reuse and avoid repetition",
                    "points": 12
                },
                "organization": {
                    "description": "Mentions that functions help organize and structure code",
                    "points": 9
                },
                "clarity": {
                    "description": "Provides clear explanation with specific benefits or examples",
                    "points": 9
                }
            },
            "passing_threshold": 60  # Need 18/30 points to pass
        }

        step2 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=2,
            step_type="CHAT",
            title="Why use functions?",
            instruction="In your own words, explain why programmers use functions in their code. What problems do functions solve? Provide at least one specific benefit.",
            rubric=rubric_step2,
            points_possible=30,
            passing_threshold=60,
            auto_narrate=True,
            gm_context="The learner is explaining the benefits of functions. Look for understanding of reusability, organization, and code clarity. Be encouraging and provide constructive feedback."
        )
        session.add(step2)

        # Step 3: CONTINUE_GATE - Transition
        step3 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=3,
            step_type="CONTINUE_GATE",
            title="Function Components",
            instruction="Excellent work so far! Now let's break down the anatomy of a function. Every function has key components that work together. Understanding these parts will help you read and write functions confidently.",
            points_possible=0,
            passing_threshold=0,
            auto_narrate=True,
            gm_context="Transition to the technical details of function structure. Build excitement about learning the components."
        )
        session.add(step3)

        # Step 4: MCQ_MULTI - Function components
        step4 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=4,
            step_type="MCQ_MULTI",
            title="Identifying function parts",
            instruction="A typical function has several key components. Select ALL the parts that are commonly found in a function definition:",
            options=[
                "Function name",          # Correct
                "Parameters (inputs)",    # Correct
                "Return value (output)",  # Correct
                "Function body (code)",   # Correct
                "Database connection",
                "CSS styles"
            ],
            correct_answers=[0, 1, 2, 3],
            points_possible=30,
            passing_threshold=75,  # Need 3 out of 4 correct
            auto_narrate=False
        )
        session.add(step4)

        # Step 5: TRUE_FALSE - Return statements
        step5 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=5,
            step_type="TRUE_FALSE",
            title="Return statements",
            instruction="True or False: Every function must have a return statement that sends a value back to the caller.",
            correct_answer=False,  # False - not all functions return values
            points_possible=20,
            passing_threshold=100,
            auto_narrate=False
        )
        session.add(step5)

        await session.commit()

        print(f"""
✅ Production Challenge Created: Introduction to Functions

Challenge ID: {challenge.id}
Difficulty: Beginner
Total Points: 100
Passing Score: 70%

Steps:
  0. CONTINUE_GATE: Welcome to Functions (0 pts, GM narration)
  1. MCQ_SINGLE: What is a function? (20 pts)
  2. CHAT: Why use functions? (30 pts, rubric: reusability, organization, clarity)
  3. CONTINUE_GATE: Function Components (0 pts, GM narration)
  4. MCQ_MULTI: Identifying function parts (30 pts, 4 correct answers)
  5. TRUE_FALSE: Return statements (20 pts)

Learning Objectives:
✓ Define what a function is
✓ Explain why functions are useful
✓ Identify key components of a function
✓ Understand return values are optional

Estimated Time: 20 minutes
XP Reward: 100
""")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_functions_challenge())
