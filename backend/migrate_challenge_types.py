"""
Migration Script: Auto-classify challenges as Simple or Advanced

This script automatically classifies existing challenges:
- Advanced: Challenges that have steps defined
- Simple: Challenges without steps

Run: python -m backend.migrate_challenge_types
"""

import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database import engine, Base
from backend.app.models import Challenge, ChallengeStep


async def migrate_challenge_types():
    """Auto-classify challenges based on presence of steps"""
    async with AsyncSession(bind=engine) as session:
        # Get all challenges
        result = await session.execute(select(Challenge))
        challenges = result.scalars().all()

        print(f"\n{'='*60}")
        print(f"Found {len(challenges)} challenges to classify")
        print(f"{'='*60}\n")

        simple_count = 0
        advanced_count = 0

        for challenge in challenges:
            # Check if challenge has steps
            steps_result = await session.execute(
                select(ChallengeStep).where(
                    ChallengeStep.challenge_id == challenge.id
                )
            )
            steps = steps_result.scalars().all()

            # Classify based on steps
            if steps:
                challenge.challenge_type = "advanced"
                classification = "Advanced"
                advanced_count += 1
                print(f"✓ {challenge.title:.<50} {classification} ({len(steps)} steps)")
            else:
                challenge.challenge_type = "simple"
                classification = "Simple"
                simple_count += 1
                print(f"✓ {challenge.title:.<50} {classification}")

            # Initialize custom_variables if not set
            if not hasattr(challenge, 'custom_variables') or challenge.custom_variables is None:
                challenge.custom_variables = {}

            session.add(challenge)

        # Commit all changes
        await session.commit()

        print(f"\n{'='*60}")
        print(f"Migration Complete!")
        print(f"{'='*60}")
        print(f"Simple challenges:   {simple_count}")
        print(f"Advanced challenges: {advanced_count}")
        print(f"Total:               {simple_count + advanced_count}")
        print(f"{'='*60}\n")


async def verify_migration():
    """Verify the migration was successful"""
    async with AsyncSession(bind=engine) as session:
        result = await session.execute(select(Challenge))
        challenges = result.scalars().all()

        print(f"\n{'='*60}")
        print("Verification Results")
        print(f"{'='*60}\n")

        for challenge in challenges:
            challenge_type = getattr(challenge, 'challenge_type', 'MISSING')
            custom_vars = getattr(challenge, 'custom_variables', 'MISSING')
            print(f"  {challenge.title}")
            print(f"    Type: {challenge_type}")
            print(f"    Custom Variables: {custom_vars}")
            print()


async def main():
    """Main migration function"""
    import sys

    print("\n" + "="*60)
    print("Challenge Type Migration Script")
    print("="*60)
    print("\nThis will classify all existing challenges as:")
    print("  - Simple: No steps (LLM-managed)")
    print("  - Advanced: Has steps (step-based)")
    print("\n" + "="*60)

    # Check for --force flag
    force = "--force" in sys.argv

    if not force:
        response = input("\nContinue with migration? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Migration cancelled.")
            return

    try:
        await migrate_challenge_types()
        print("\nRunning verification...")
        await verify_migration()
        print("✓ Migration successful!")
    except Exception as e:
        print(f"\n✗ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
