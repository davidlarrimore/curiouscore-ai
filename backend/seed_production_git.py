"""
Production Challenge: Git Basics - Commits & Branches

An intermediate-level challenge teaching version control fundamentals
with Git. Covers commits, commit messages, branches, and workflows.

Total: 150 points | Passing: 70%
"""

import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.database import Base
from app.models import Challenge, ChallengeStep, User
from app.config import settings


async def seed_git_challenge():
    """Create 'Git Basics' production challenge."""
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
            select(Challenge).where(Challenge.title == "Git Basics: Commits & Branches")
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
            print("✅ Deleted existing 'Git Basics' challenge")

        # Create challenge
        challenge_id = str(uuid.uuid4())
        challenge = Challenge(
            id=challenge_id,
            title="Git Basics: Commits & Branches",
            description="Learn version control fundamentals with Git. Understand commits, write great commit messages, work with branches, and follow professional workflows.",
            tags=["intermediate", "git", "version-control", "collaboration"],
            difficulty="intermediate",
            system_prompt="Teaching Git version control fundamentals for professional development",
            estimated_time_minutes=25,
            xp_reward=150,
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
            title="Welcome to Git",
            instruction="Welcome to Git Basics! Version control is an essential skill for every developer. Git helps you track changes, collaborate with others, and maintain a complete history of your project. In this challenge, you'll learn the core concepts that professional developers use every day.",
            points_possible=0,
            passing_threshold=0,
            auto_narrate=True,
            gm_context="Introduction to Git for intermediate learners. Set a professional but supportive tone. Emphasize the real-world importance of version control."
        )
        session.add(step0)

        # Step 1: CHAT - What is a commit?
        rubric_step1 = {
            "total_points": 30,
            "criteria": {
                "snapshot": {
                    "description": "Explains that a commit is a snapshot of the project at a point in time",
                    "points": 15
                },
                "tracking": {
                    "description": "Mentions that commits track changes or create history",
                    "points": 10
                },
                "clarity": {
                    "description": "Provides clear explanation with understanding of the concept",
                    "points": 5
                }
            },
            "passing_threshold": 60  # Need 18/30 points to pass
        }

        step1 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=1,
            step_type="CHAT",
            title="Understanding commits",
            instruction="In your own words, explain what a Git commit is. What does a commit represent, and why is it important in version control?",
            rubric=rubric_step1,
            points_possible=30,
            passing_threshold=60,
            auto_narrate=True,
            gm_context="The learner is explaining commits. Look for understanding of snapshots, change tracking, and project history. Encourage precise thinking about version control."
        )
        session.add(step1)

        # Step 2: MCQ_SINGLE - Commit message best practice
        step2 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=2,
            step_type="MCQ_SINGLE",
            title="Writing commit messages",
            instruction="You've just fixed a bug where user login was failing. Which commit message follows best practices?",
            options=[
                "Fix user login authentication bug",  # Correct - clear, concise, imperative mood
                "fixed stuff",
                "Updated some files in the auth folder idk",
                "I spent 3 hours debugging the login system and finally found that the password validation was broken so I fixed it by updating the hash comparison"
            ],
            correct_answer=0,
            points_possible=25,
            passing_threshold=100,
            auto_narrate=False
        )
        session.add(step2)

        # Step 3: CHAT - Why branches?
        rubric_step3 = {
            "total_points": 40,
            "criteria": {
                "isolation": {
                    "description": "Explains that branches isolate work or allow parallel development",
                    "points": 16
                },
                "example": {
                    "description": "Provides a practical example or use case for branching",
                    "points": 16
                },
                "completeness": {
                    "description": "Demonstrates complete understanding with clear reasoning",
                    "points": 8
                }
            },
            "passing_threshold": 65  # Need 26/40 points to pass
        }

        step3 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=3,
            step_type="CHAT",
            title="Why use branches?",
            instruction="Explain why developers use branches in Git. What problem do branches solve? Provide a practical example of when you'd create a branch.",
            rubric=rubric_step3,
            points_possible=40,
            passing_threshold=65,
            auto_narrate=True,
            gm_context="The learner is explaining Git branches. Look for understanding of work isolation, parallel development, and feature workflows. Encourage practical thinking with examples."
        )
        session.add(step3)

        # Step 4: CONTINUE_GATE - Scenario setup
        step4 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=4,
            step_type="CONTINUE_GATE",
            title="Feature development workflow",
            instruction="Great! Now let's put this into practice. Imagine you're working on a team, and you need to add a new feature to your application. Let's walk through the proper Git workflow for this scenario.",
            points_possible=0,
            passing_threshold=0,
            auto_narrate=True,
            gm_context="Build anticipation for the practical workflow question. Make it feel real and applicable to their work."
        )
        session.add(step4)

        # Step 5: MCQ_MULTI - Feature workflow steps
        step5 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=5,
            step_type="MCQ_MULTI",
            title="Git feature workflow",
            instruction="You're adding a new user profile feature. Select ALL the steps that are part of a proper Git feature branch workflow (in any order):",
            options=[
                "Create a new branch from main",              # Correct
                "Make commits on your feature branch",        # Correct
                "Push your branch to the remote repository",  # Correct
                "Merge your branch back to main",             # Correct
                "Delete all previous commits",
                "Rewrite the main branch history"
            ],
            correct_answers=[0, 1, 2, 3],
            points_possible=35,
            passing_threshold=75,  # Need 3 out of 4 correct
            auto_narrate=False
        )
        session.add(step5)

        # Step 6: TRUE_FALSE - Delete branch after merge
        step6 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=6,
            step_type="TRUE_FALSE",
            title="Branch cleanup",
            instruction="True or False: After successfully merging a feature branch into main, it's safe (and common practice) to delete the feature branch.",
            correct_answer=True,  # True - branches are typically deleted after merging
            points_possible=20,
            passing_threshold=100,
            auto_narrate=False
        )
        session.add(step6)

        await session.commit()

        print(f"""
✅ Production Challenge Created: Git Basics - Commits & Branches

Challenge ID: {challenge.id}
Difficulty: Intermediate
Total Points: 150
Passing Score: 70%

Steps:
  0. CONTINUE_GATE: Welcome to Git (0 pts, GM narration)
  1. CHAT: Understanding commits (30 pts, rubric: snapshot, tracking, clarity)
  2. MCQ_SINGLE: Writing commit messages (25 pts)
  3. CHAT: Why use branches? (40 pts, rubric: isolation, example, completeness)
  4. CONTINUE_GATE: Feature development workflow (0 pts, GM narration)
  5. MCQ_MULTI: Git feature workflow (35 pts, 4 correct answers)
  6. TRUE_FALSE: Branch cleanup (20 pts)

Learning Objectives:
✓ Understand what commits represent
✓ Write clear commit messages
✓ Explain the purpose of branches
✓ Follow proper feature branch workflow
✓ Know when to delete branches

Estimated Time: 25 minutes
XP Reward: 150
""")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_git_challenge())
