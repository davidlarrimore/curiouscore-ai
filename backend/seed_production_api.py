"""
Production Challenge: API Design Principles

An advanced-level challenge teaching RESTful API design best practices.
Covers REST principles, HTTP methods, URL design, status codes, and error handling.

Total: 200 points | Passing: 75%
"""

import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.database import Base
from app.models import Challenge, ChallengeStep, User
from app.config import settings


async def seed_api_challenge():
    """Create 'API Design Principles' production challenge."""
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
            select(Challenge).where(Challenge.title == "API Design Principles")
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
            print("✅ Deleted existing 'API Design Principles' challenge")

        # Create challenge
        challenge_id = str(uuid.uuid4())
        challenge = Challenge(
            id=challenge_id,
            title="API Design Principles",
            description="Master RESTful API design. Learn industry best practices for building clean, consistent, and scalable APIs that developers love to use.",
            tags=["advanced", "api", "rest", "backend", "architecture"],
            difficulty="advanced",
            system_prompt="Teaching professional API design principles and RESTful architecture",
            estimated_time_minutes=30,
            xp_reward=200,
            passing_score=75,
            is_active=True
        )
        session.add(challenge)
        await session.commit()
        print(f"✅ Created challenge: {challenge.id}")

        # Step 0: CONTINUE_GATE - Introduction
        step0 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=0,
            step_type="CONTINUE_GATE",
            title="Welcome to API Design",
            instruction="Welcome to API Design Principles! This is an advanced topic that separates good developers from great ones. Well-designed APIs are intuitive, consistent, and scalable. Poorly designed APIs frustrate developers and create technical debt. In this challenge, you'll learn the principles that power the world's best APIs.",
            points_possible=0,
            passing_threshold=0,
            auto_narrate=True,
            gm_context="Introduction to advanced API design. Set a professional, high-bar tone. Emphasize that this is expert-level knowledge with real-world impact."
        )
        session.add(step0)

        # Step 1: CHAT - Explain REST
        rubric_step1 = {
            "total_points": 40,
            "criteria": {
                "resources": {
                    "description": "Explains that REST uses resources (nouns) not actions",
                    "points": 13
                },
                "http_methods": {
                    "description": "Mentions standard HTTP methods (GET, POST, PUT, DELETE)",
                    "points": 13
                },
                "stateless": {
                    "description": "References stateless communication or standard conventions",
                    "points": 14
                }
            },
            "passing_threshold": 60  # Need 24/40 points to pass
        }

        step1 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=1,
            step_type="CHAT",
            title="What is REST?",
            instruction="Explain the key principles of RESTful API design. What makes an API 'RESTful'? Describe at least two core characteristics.",
            rubric=rubric_step1,
            points_possible=40,
            passing_threshold=60,
            auto_narrate=True,
            gm_context="The learner is explaining REST principles. Look for understanding of resources, HTTP methods, and stateless architecture. Expect precise technical knowledge."
        )
        session.add(step1)

        # Step 2: MCQ_SINGLE - HTTP method for updating
        step2 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=2,
            step_type="MCQ_SINGLE",
            title="Updating a resource",
            instruction="A client wants to update an existing user's email address. Which HTTP method should your API endpoint use?",
            options=[
                "PUT or PATCH",  # Correct - both are valid for updates
                "GET",
                "POST",
                "DELETE"
            ],
            correct_answer=0,
            points_possible=30,
            passing_threshold=100,
            auto_narrate=False
        )
        session.add(step2)

        # Step 3: CHAT - Design RESTful URLs
        rubric_step3 = {
            "total_points": 50,
            "criteria": {
                "plural_nouns": {
                    "description": "Uses plural nouns for collections (e.g., /users not /user)",
                    "points": 13
                },
                "path_params": {
                    "description": "Uses path parameters for IDs (e.g., /users/123)",
                    "points": 12
                },
                "no_verbs": {
                    "description": "Avoids verbs in URLs (HTTP methods provide the action)",
                    "points": 13
                },
                "explanation": {
                    "description": "Explains reasoning or provides clear examples",
                    "points": 12
                }
            },
            "passing_threshold": 65  # Need 32.5/50 points to pass
        }

        step3 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=3,
            step_type="CHAT",
            title="URL design patterns",
            instruction="Design RESTful URL patterns for a blog API that manages posts and comments. Provide at least 3 example URLs and explain why they follow REST best practices.",
            rubric=rubric_step3,
            points_possible=50,
            passing_threshold=65,
            auto_narrate=True,
            gm_context="The learner is designing RESTful URLs. Look for plural nouns, path parameters, no verbs, and hierarchical relationships. Expect professional API design."
        )
        session.add(step3)

        # Step 4: CONTINUE_GATE - Status codes transition
        step4 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=4,
            step_type="CONTINUE_GATE",
            title="HTTP Status Codes",
            instruction="Excellent URL design! Now let's talk about how your API communicates success and failure. HTTP status codes are a critical part of RESTful APIs—they tell clients exactly what happened with their request.",
            points_possible=0,
            passing_threshold=0,
            auto_narrate=True,
            gm_context="Transition to status codes. Build on their URL design success and set up the importance of proper status communication."
        )
        session.add(step4)

        # Step 5: MCQ_MULTI - Status codes for creation
        step5 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=5,
            step_type="MCQ_MULTI",
            title="Successful resource creation",
            instruction="A client sends a POST request to create a new resource, and the server successfully creates it. Which HTTP status code(s) are appropriate responses? Select ALL that apply:",
            options=[
                "201 Created",        # Correct - most common for successful creation
                "200 OK",             # Correct - also acceptable for successful creation
                "204 No Content",     # Correct - valid if no body returned
                "400 Bad Request",
                "500 Internal Server Error"
            ],
            correct_answers=[0, 1, 2],
            points_possible=35,
            passing_threshold=66,  # Need 2 out of 3 correct
            auto_narrate=False
        )
        session.add(step5)

        # Step 6: CHAT - Error handling best practices
        rubric_step6 = {
            "total_points": 45,
            "criteria": {
                "status_codes": {
                    "description": "Mentions using appropriate HTTP status codes for errors",
                    "points": 15
                },
                "error_messages": {
                    "description": "Describes clear, helpful error messages or response bodies",
                    "points": 15
                },
                "consistency": {
                    "description": "Emphasizes consistent error format or structure",
                    "points": 15
                }
            },
            "passing_threshold": 65  # Need 29/45 points to pass
        }

        step6 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=6,
            step_type="CHAT",
            title="API error handling",
            instruction="Describe best practices for handling and communicating errors in a RESTful API. What information should error responses include, and how should they be structured?",
            rubric=rubric_step6,
            points_possible=45,
            passing_threshold=65,
            auto_narrate=True,
            gm_context="The learner is explaining error handling. Look for understanding of status codes, clear messages, and consistent structure. This is expert-level API design."
        )
        session.add(step6)

        await session.commit()

        print(f"""
✅ Production Challenge Created: API Design Principles

Challenge ID: {challenge.id}
Difficulty: Advanced
Total Points: 200
Passing Score: 75%

Steps:
  0. CONTINUE_GATE: Welcome to API Design (0 pts, GM narration)
  1. CHAT: What is REST? (40 pts, rubric: resources, HTTP methods, stateless)
  2. MCQ_SINGLE: Updating a resource (30 pts)
  3. CHAT: URL design patterns (50 pts, rubric: plural nouns, path params, no verbs)
  4. CONTINUE_GATE: HTTP Status Codes (0 pts, GM narration)
  5. MCQ_MULTI: Successful resource creation (35 pts, 3 correct answers)
  6. CHAT: API error handling (45 pts, rubric: status codes, messages, consistency)

Learning Objectives:
✓ Understand RESTful principles
✓ Choose appropriate HTTP methods
✓ Design clean, consistent URL patterns
✓ Use proper HTTP status codes
✓ Implement professional error handling

Estimated Time: 30 minutes
XP Reward: 200
""")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_api_challenge())
