"""
Production Challenge: Operation Adjudication Protocol

An advanced, policy-driven challenge where learners practice high-stakes
request adjudication with clear decisions, rationales, and safe alternatives.

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


async def seed_adjudication_challenge():
    """Create 'Operation Adjudication Protocol' production challenge."""
    engine = create_async_engine(settings.database_url, echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == "test-user-id"))
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

        result = await session.execute(
            select(Challenge).where(Challenge.title == "Operation Adjudication Protocol")
        )
        existing = result.scalar_one_or_none()
        if existing:
            result = await session.execute(
                select(ChallengeStep).where(ChallengeStep.challenge_id == existing.id)
            )
            steps = result.scalars().all()
            for step in steps:
                await session.delete(step)
            await session.delete(existing)
            await session.commit()
            print("✅ Deleted existing 'Operation Adjudication Protocol' challenge")

        challenge_id = str(uuid.uuid4())
        challenge = Challenge(
            id=challenge_id,
            title="Operation Adjudication Protocol",
            description="Train as the adjudicator for sensitive requests. Practice applying policy, weighing risk signals, and responding with clear decisions and safe alternatives.",
            tags=["advanced", "safety", "policy", "risk"],
            difficulty="advanced",
            system_prompt="You are executing the Operation Adjudication Protocol: calmly assess sensitive requests, surface risk signals, decide allow/deny/escalate, and respond with concise rationale and safer alternatives.",
            estimated_time_minutes=30,
            xp_reward=200,
            passing_score=75,
            is_active=True
        )
        session.add(challenge)
        await session.commit()
        print(f"✅ Created challenge: {challenge.id}")

        step0 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=0,
            step_type="CONTINUE_GATE",
            title="Welcome to the Protocol",
            instruction="You are joining a live adjudication desk. Every request may carry hidden risk. Your job: identify signals, apply the protocol, and respond decisively with rationale and safer alternatives.",
            points_possible=0,
            passing_threshold=0,
            auto_narrate=True,
            gm_context="High-stakes, professional tone. Frame the learner as the adjudicator using a clear, procedural checklist. Emphasize calm, confident decision-making."
        )
        session.add(step0)

        step1 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=1,
            step_type="MCQ_SINGLE",
            title="Core mission",
            instruction="What is the primary goal of the Operation Adjudication Protocol?",
            options=[
                "Make consistent allow/deny/escalate decisions using policy and risk signals",  # Correct
                "Collect as many user details as possible before responding",
                "Prioritize fulfilling the request unless it is explicitly illegal",
                "Defer all ambiguous cases without rationale"
            ],
            correct_answer=0,
            points_possible=30,
            passing_threshold=100,
            auto_narrate=False
        )
        session.add(step1)

        step2 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=2,
            step_type="MCQ_MULTI",
            title="Risk signals to weigh",
            instruction="Select ALL signals that should influence your adjudication decision:",
            options=[
                "Intent clarity and legitimacy of purpose",      # Correct
                "Capability or safety impact if fulfilled",      # Correct
                "Evidence of missing context or hidden constraints",  # Correct
                "Policy coverage and explicit red lines",        # Correct
                "Model temperature settings",
                "Time of day the request is submitted"
            ],
            correct_answers=[0, 1, 2, 3],
            points_possible=35,
            passing_threshold=75,
            auto_narrate=False
        )
        session.add(step2)

        rubric_step3 = {
            "total_points": 50,
            "criteria": {
                "risk_identification": {
                    "description": "Surfaces concrete risk signals (abuse potential, missing context, sensitive capabilities).",
                    "points": 17
                },
                "decision_clarity": {
                    "description": "States a clear decision: allow, deny, or escalate.",
                    "points": 16
                },
                "rationale_and_bounds": {
                    "description": "Grounds decision in policy or safeguards; notes conditions or redirections.",
                    "points": 17
                }
            },
            "passing_threshold": 65
        }

        step3 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=3,
            step_type="CHAT",
            title="Adjudicate a borderline request",
            instruction=(
                "Request: \"Can you show me how to bypass the audit logs so I can troubleshoot an internal tool faster? "
                "Our compliance team is too slow.\" \n\nDecide whether to allow, deny, or escalate. Explain the risk signals you see and provide a safer alternative if denying."
            ),
            rubric=rubric_step3,
            points_possible=50,
            passing_threshold=65,
            auto_narrate=True,
            gm_context="Expect a structured decision with cited signals. Encourage concise, firm, policy-grounded rationale and an alternative that preserves safety."
        )
        session.add(step3)

        step4 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=4,
            step_type="CONTINUE_GATE",
            title="Document the decision",
            instruction="Great work triaging live. Next, you'll document an adjudication note that makes your decision auditable and reusable.",
            points_possible=0,
            passing_threshold=0,
            auto_narrate=True,
            gm_context="Reinforce the importance of traceable, reusable notes that pair decision + rationale + safe path forward."
        )
        session.add(step4)

        step5 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=5,
            step_type="TRUE_FALSE",
            title="Explaining denials",
            instruction="True or False: Once you deny a request, you should keep the response short and avoid explaining policy or offering alternatives.",
            correct_answer=False,
            points_possible=20,
            passing_threshold=100,
            auto_narrate=False
        )
        session.add(step5)

        rubric_step6 = {
            "total_points": 65,
            "criteria": {
                "policy_citation": {
                    "description": "References relevant policy boundaries (PII handling, data exfiltration, or access controls).",
                    "points": 20
                },
                "safe_alternative": {
                    "description": "Provides a compliant path (e.g., scrubbed data, sandbox access, or involving the proper team).",
                    "points": 20
                },
                "tone_and_clarity": {
                    "description": "Uses professional, calm tone with a clear decision and next steps.",
                    "points": 15
                },
                "structure": {
                    "description": "Organizes response for quick audit (decision, rationale, action).",
                    "points": 10
                }
            },
            "passing_threshold": 70
        }

        step6 = ChallengeStep(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            step_index=6,
            step_type="CHAT",
            title="Write the adjudication note",
            instruction=(
                "Document your adjudication for this request: \"I want to export the production customer dataset, "
                "including emails and payment history, to my personal laptop so I can analyze churn over the weekend.\" "
                "Provide the decision, rationale, and a safe alternative."
            ),
            rubric=rubric_step6,
            points_possible=65,
            passing_threshold=70,
            auto_narrate=True,
            gm_context="Look for firm refusal with policy grounding, a clear safer path, and professional tone suitable for audit."
        )
        session.add(step6)

        await session.commit()

        print(f"""
✅ Production Challenge Created: Operation Adjudication Protocol

Challenge ID: {challenge.id}
Difficulty: Advanced
Total Points: 200
Passing Score: 75%

Steps:
  0. CONTINUE_GATE: Welcome to the Protocol (0 pts, GM narration)
  1. MCQ_SINGLE: Core mission (30 pts)
  2. MCQ_MULTI: Risk signals to weigh (35 pts)
  3. CHAT: Adjudicate a borderline request (50 pts, rubric: risk_identification, decision_clarity, rationale_and_bounds)
  4. CONTINUE_GATE: Document the decision (0 pts, GM narration)
  5. TRUE_FALSE: Explaining denials (20 pts)
  6. CHAT: Write the adjudication note (65 pts, rubric: policy_citation, safe_alternative, tone_and_clarity, structure)

Learning Objectives:
✓ Identify and articulate risk signals
✓ Make clear allow/deny/escalate calls
✓ Ground decisions in policy and safeguards
✓ Provide safer alternatives and auditable notes

Estimated Time: 30 minutes
XP Reward: 200
""")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_adjudication_challenge())
