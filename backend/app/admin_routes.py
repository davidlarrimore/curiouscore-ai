"""
Admin API Routes for Game Master Architecture

Provides full CRUD operations for:
- Challenges
- ChallengeSteps
- Personas
- Scenes
- MediaAssets
- KnowledgeBase

All endpoints require admin authorization.
"""

import uuid
import math
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from .database import get_session
from .deps import require_admin

logger = logging.getLogger(__name__)
from .models import (
    User,
    Challenge,
    ChallengeModel,
    ChallengeStep,
    Persona,
    Scene,
    MediaAsset,
    KnowledgeBase,
)
from .schemas import (
    ChallengeCreate,
    ChallengeUpdate,
    ChallengeOut,
    ChallengeOutDetailed,
    ChallengeStepCreate,
    ChallengeStepUpdate,
    ChallengeStepOut,
    PersonaCreate,
    PersonaUpdate,
    PersonaOut,
    SceneCreate,
    SceneUpdate,
    SceneOut,
    MediaAssetOut,
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseOut,
    StepReorderRequest,
    ChallengeActivationUpdate,
    ChallengePromptUpdate,
    ChallengeModelOut,
    ChallengeModelUpdate,
)

router = APIRouter(prefix="/admin", tags=["admin"])


# ============================================================================
# Challenge CRUD
# ============================================================================

@router.get("/challenges/models", response_model=List[ChallengeModelOut])
async def get_challenge_models(
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """List challenge-to-LLM model mappings."""
    result = await db.execute(select(ChallengeModel))
    return result.scalars().all()


@router.put("/challenges/{challenge_id}/model", response_model=ChallengeModelOut)
async def set_challenge_model(
    challenge_id: str,
    payload: ChallengeModelUpdate,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """Create or update the LLM provider/model mapping for a challenge."""
    challenge_result = await db.execute(
        select(Challenge)
        .options(selectinload(Challenge.llm_config))
        .where(Challenge.id == challenge_id)
    )
    challenge = challenge_result.scalars().first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    existing_result = await db.execute(
        select(ChallengeModel).where(ChallengeModel.challenge_id == challenge_id)
    )
    existing = existing_result.scalars().first()

    if existing:
        existing.provider = payload.provider
        existing.model = payload.model
        db.add(existing)
        await db.commit()
        await db.refresh(existing)
        return existing

    new_mapping = ChallengeModel(
        challenge_id=challenge_id,
        provider=payload.provider,
        model=payload.model,
    )
    db.add(new_mapping)
    await db.commit()
    await db.refresh(new_mapping)
    return new_mapping


@router.post("/challenges", response_model=ChallengeOut)
async def create_challenge(
    payload: ChallengeCreate,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """Create a new challenge."""
    challenge = Challenge(
        id=str(uuid.uuid4()),
        **payload.model_dump(),
    )
    db.add(challenge)
    await db.commit()
    await db.refresh(challenge)
    return challenge


@router.get("/challenges", response_model=dict)
async def list_challenges(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    difficulty: Optional[str] = None,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """
    List all challenges with pagination and filtering.
    Returns both active and inactive challenges.
    """
    # Build query - load llm_config and steps for count
    stmt = select(Challenge).options(
        selectinload(Challenge.llm_config),
        selectinload(Challenge.steps)
    )

    # Apply filters
    if search:
        search_term = f"%{search}%"
        stmt = stmt.where(
            or_(
                Challenge.title.ilike(search_term),
                Challenge.description.ilike(search_term),
            )
        )
    if difficulty:
        stmt = stmt.where(Challenge.difficulty == difficulty)

    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * limit
    stmt = stmt.offset(offset).limit(limit).order_by(Challenge.created_at.desc())

    # Execute query
    result = await db.execute(stmt)
    challenges = result.scalars().all()

    # Build response items with step count
    items = []
    for challenge in challenges:
        challenge_dict = ChallengeOut.model_validate(challenge).model_dump()
        challenge_dict['step_count'] = len(challenge.steps)
        items.append(challenge_dict)

    return {
        "items": items,
        "total": total,
        "page": page,
        "pages": math.ceil(total / limit) if total > 0 else 0,
        "limit": limit,
    }


@router.get("/challenges/{challenge_id}", response_model=ChallengeOutDetailed)
async def get_challenge_detailed(
    challenge_id: str,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """Get challenge with all relationships loaded (steps, personas, scenes, knowledge_base)."""
    stmt = (
        select(Challenge)
        .options(
            selectinload(Challenge.llm_config),
            selectinload(Challenge.steps),
            selectinload(Challenge.personas),
            selectinload(Challenge.scenes),
            selectinload(Challenge.knowledge_base),
        )
        .where(Challenge.id == challenge_id)
    )
    result = await db.execute(stmt)
    challenge = result.scalars().first()

    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    print(f"========== GET CHALLENGE {challenge_id} ==========")
    print(f"custom_variables from DB: {challenge.custom_variables}")

    return challenge


@router.patch("/challenges/{challenge_id}", response_model=ChallengeOut)
async def update_challenge(
    challenge_id: str,
    payload: ChallengeUpdate,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """Update challenge fields."""
    # Debug logging
    update_data = payload.model_dump(exclude_unset=True)
    print(f"========== UPDATE CHALLENGE {challenge_id} ==========")
    print(f"Received update data: {update_data}")
    logger.info(f"UPDATE CHALLENGE {challenge_id}")
    logger.info(f"Received update data: {update_data}")

    stmt = select(Challenge).where(Challenge.id == challenge_id)
    result = await db.execute(stmt)
    challenge = result.scalars().first()

    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    # Update fields
    for field, value in update_data.items():
        print(f"Setting {field} = {value[:100] if isinstance(value, str) else value}")
        logger.info(f"Setting {field} = {value}")
        setattr(challenge, field, value)

    await db.commit()
    await db.refresh(challenge)

    print(f"Challenge after update - custom_variables: {challenge.custom_variables}")
    logger.info(f"Challenge after update - custom_variables: {challenge.custom_variables}")
    return challenge


@router.delete("/challenges/{challenge_id}")
async def delete_challenge(
    challenge_id: str,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """Delete challenge and all related entities (cascade)."""
    stmt = select(Challenge).where(Challenge.id == challenge_id)
    result = await db.execute(stmt)
    challenge = result.scalars().first()

    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    await db.delete(challenge)
    await db.commit()
    return {"message": "Challenge deleted successfully"}


# Backward-compatible endpoints for old Admin.tsx
@router.patch("/challenges/{challenge_id}/activation", response_model=ChallengeOut)
async def update_challenge_activation_compat(
    challenge_id: str,
    payload: ChallengeActivationUpdate,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """Update challenge activation status (backward compatible)."""
    stmt = select(Challenge).options(selectinload(Challenge.llm_config)).where(Challenge.id == challenge_id)
    result = await db.execute(stmt)
    challenge = result.scalars().first()

    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    challenge.is_active = payload.is_active
    await db.commit()
    await db.refresh(challenge)
    return challenge


@router.patch("/challenges/{challenge_id}/prompt", response_model=ChallengeOut)
async def update_challenge_prompt_compat(
    challenge_id: str,
    payload: ChallengePromptUpdate,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """Update challenge system prompt (backward compatible)."""
    stmt = select(Challenge).options(selectinload(Challenge.llm_config)).where(Challenge.id == challenge_id)
    result = await db.execute(stmt)
    challenge = result.scalars().first()

    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    challenge.system_prompt = payload.system_prompt
    await db.commit()
    await db.refresh(challenge)
    return challenge


# ============================================================================
# ChallengeStep CRUD
# ============================================================================

@router.post("/challenges/{challenge_id}/steps", response_model=ChallengeStepOut)
async def create_challenge_step(
    challenge_id: str,
    payload: ChallengeStepCreate,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """Create a new step for a challenge."""
    # Verify challenge exists
    stmt = select(Challenge).where(Challenge.id == challenge_id)
    result = await db.execute(stmt)
    challenge = result.scalars().first()

    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    # Ensure challenge_id matches
    if payload.challenge_id != challenge_id:
        raise HTTPException(status_code=400, detail="Challenge ID mismatch")

    step = ChallengeStep(
        id=str(uuid.uuid4()),
        **payload.model_dump(),
    )
    db.add(step)
    await db.commit()
    await db.refresh(step)
    return step


@router.get("/challenges/{challenge_id}/steps", response_model=List[ChallengeStepOut])
async def list_challenge_steps(
    challenge_id: str,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """List all steps for a challenge, ordered by step_index."""
    stmt = (
        select(ChallengeStep)
        .where(ChallengeStep.challenge_id == challenge_id)
        .order_by(ChallengeStep.step_index)
    )
    result = await db.execute(stmt)
    steps = result.scalars().all()
    return steps


@router.get("/challenges/{challenge_id}/steps/{step_id}", response_model=ChallengeStepOut)
async def get_challenge_step(
    challenge_id: str,
    step_id: str,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """Get a specific challenge step."""
    stmt = (
        select(ChallengeStep)
        .where(ChallengeStep.id == step_id, ChallengeStep.challenge_id == challenge_id)
    )
    result = await db.execute(stmt)
    step = result.scalars().first()

    if not step:
        raise HTTPException(status_code=404, detail="Step not found")

    return step


@router.patch("/challenges/{challenge_id}/steps/{step_id}", response_model=ChallengeStepOut)
async def update_challenge_step(
    challenge_id: str,
    step_id: str,
    payload: ChallengeStepUpdate,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """Update a challenge step."""
    stmt = (
        select(ChallengeStep)
        .where(ChallengeStep.id == step_id, ChallengeStep.challenge_id == challenge_id)
    )
    result = await db.execute(stmt)
    step = result.scalars().first()

    if not step:
        raise HTTPException(status_code=404, detail="Step not found")

    # Update fields
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(step, field, value)

    await db.commit()
    await db.refresh(step)
    return step


@router.delete("/challenges/{challenge_id}/steps/{step_id}")
async def delete_challenge_step(
    challenge_id: str,
    step_id: str,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """Delete a challenge step."""
    stmt = (
        select(ChallengeStep)
        .where(ChallengeStep.id == step_id, ChallengeStep.challenge_id == challenge_id)
    )
    result = await db.execute(stmt)
    step = result.scalars().first()

    if not step:
        raise HTTPException(status_code=404, detail="Step not found")

    await db.delete(step)
    await db.commit()
    return {"message": "Step deleted successfully"}


@router.patch("/challenges/{challenge_id}/steps/reorder", response_model=List[ChallengeStepOut])
async def reorder_challenge_steps(
    challenge_id: str,
    payload: StepReorderRequest,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """Reorder steps by providing ordered list of step IDs."""
    # Fetch all steps
    stmt = select(ChallengeStep).where(ChallengeStep.challenge_id == challenge_id)
    result = await db.execute(stmt)
    steps = {step.id: step for step in result.scalars().all()}

    # Validate all step IDs exist
    if set(payload.step_ids) != set(steps.keys()):
        raise HTTPException(status_code=400, detail="Step IDs mismatch")

    # Update step_index
    for index, step_id in enumerate(payload.step_ids):
        steps[step_id].step_index = index

    await db.commit()

    # Return ordered steps
    return [steps[step_id] for step_id in payload.step_ids]


# ============================================================================
# Persona CRUD
# ============================================================================

@router.post("/personas", response_model=PersonaOut)
async def create_persona(
    payload: PersonaCreate,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """Create a new persona (global or challenge-specific)."""
    persona = Persona(
        id=str(uuid.uuid4()),
        **payload.model_dump(),
    )
    db.add(persona)
    await db.commit()
    await db.refresh(persona)
    return persona


@router.get("/personas", response_model=List[PersonaOut])
async def list_personas(
    challenge_id: Optional[str] = None,
    global_only: bool = False,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """List personas, optionally filtered by challenge or global-only."""
    stmt = select(Persona)

    if global_only:
        stmt = stmt.where(Persona.challenge_id.is_(None))
    elif challenge_id:
        stmt = stmt.where(
            or_(Persona.challenge_id == challenge_id, Persona.challenge_id.is_(None))
        )

    stmt = stmt.order_by(Persona.name)
    result = await db.execute(stmt)
    personas = result.scalars().all()
    return personas


@router.get("/personas/{persona_id}", response_model=PersonaOut)
async def get_persona(
    persona_id: str,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """Get a specific persona."""
    stmt = select(Persona).where(Persona.id == persona_id)
    result = await db.execute(stmt)
    persona = result.scalars().first()

    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    return persona


@router.patch("/personas/{persona_id}", response_model=PersonaOut)
async def update_persona(
    persona_id: str,
    payload: PersonaUpdate,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """Update a persona."""
    stmt = select(Persona).where(Persona.id == persona_id)
    result = await db.execute(stmt)
    persona = result.scalars().first()

    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    # Update fields
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(persona, field, value)

    await db.commit()
    await db.refresh(persona)
    return persona


@router.delete("/personas/{persona_id}")
async def delete_persona(
    persona_id: str,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """Delete a persona."""
    stmt = select(Persona).where(Persona.id == persona_id)
    result = await db.execute(stmt)
    persona = result.scalars().first()

    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    await db.delete(persona)
    await db.commit()
    return {"message": "Persona deleted successfully"}


# ============================================================================
# Scene CRUD
# ============================================================================

@router.post("/challenges/{challenge_id}/scenes", response_model=SceneOut)
async def create_scene(
    challenge_id: str,
    payload: SceneCreate,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """Create a new scene for a challenge."""
    # Verify challenge exists
    stmt = select(Challenge).where(Challenge.id == challenge_id)
    result = await db.execute(stmt)
    challenge = result.scalars().first()

    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    # Ensure challenge_id matches
    if payload.challenge_id != challenge_id:
        raise HTTPException(status_code=400, detail="Challenge ID mismatch")

    scene = Scene(
        id=str(uuid.uuid4()),
        **payload.model_dump(),
    )
    db.add(scene)
    await db.commit()
    await db.refresh(scene)
    return scene


@router.get("/challenges/{challenge_id}/scenes", response_model=List[SceneOut])
async def list_challenge_scenes(
    challenge_id: str,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """List all scenes for a challenge, ordered by scene_index."""
    stmt = (
        select(Scene)
        .where(Scene.challenge_id == challenge_id)
        .order_by(Scene.scene_index)
    )
    result = await db.execute(stmt)
    scenes = result.scalars().all()
    return scenes


@router.patch("/challenges/{challenge_id}/scenes/{scene_id}", response_model=SceneOut)
async def update_scene(
    challenge_id: str,
    scene_id: str,
    payload: SceneUpdate,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """Update a scene."""
    stmt = (
        select(Scene)
        .where(Scene.id == scene_id, Scene.challenge_id == challenge_id)
    )
    result = await db.execute(stmt)
    scene = result.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    # Update fields
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(scene, field, value)

    await db.commit()
    await db.refresh(scene)
    return scene


@router.delete("/challenges/{challenge_id}/scenes/{scene_id}")
async def delete_scene(
    challenge_id: str,
    scene_id: str,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """Delete a scene."""
    stmt = (
        select(Scene)
        .where(Scene.id == scene_id, Scene.challenge_id == challenge_id)
    )
    result = await db.execute(stmt)
    scene = result.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    await db.delete(scene)
    await db.commit()
    return {"message": "Scene deleted successfully"}


# ============================================================================
# MediaAsset CRUD (Simple list/delete - upload handled separately)
# ============================================================================

@router.get("/media", response_model=List[MediaAssetOut])
async def list_media_assets(
    challenge_id: Optional[str] = None,
    asset_type: Optional[str] = None,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """List media assets, optionally filtered by challenge or type."""
    stmt = select(MediaAsset)

    if challenge_id:
        stmt = stmt.where(MediaAsset.challenge_id == challenge_id)
    if asset_type:
        stmt = stmt.where(MediaAsset.asset_type == asset_type)

    stmt = stmt.order_by(MediaAsset.created_at.desc())
    result = await db.execute(stmt)
    assets = result.scalars().all()
    return assets


@router.get("/media/{asset_id}", response_model=MediaAssetOut)
async def get_media_asset(
    asset_id: str,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """Get a specific media asset."""
    stmt = select(MediaAsset).where(MediaAsset.id == asset_id)
    result = await db.execute(stmt)
    asset = result.scalars().first()

    if not asset:
        raise HTTPException(status_code=404, detail="Media asset not found")

    return asset


@router.delete("/media/{asset_id}")
async def delete_media_asset(
    asset_id: str,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """Delete a media asset."""
    stmt = select(MediaAsset).where(MediaAsset.id == asset_id)
    result = await db.execute(stmt)
    asset = result.scalars().first()

    if not asset:
        raise HTTPException(status_code=404, detail="Media asset not found")

    # TODO: Also delete physical file from storage
    await db.delete(asset)
    await db.commit()
    return {"message": "Media asset deleted successfully"}


# ============================================================================
# KnowledgeBase CRUD
# ============================================================================

@router.post("/knowledge", response_model=KnowledgeBaseOut)
async def create_knowledge_base(
    payload: KnowledgeBaseCreate,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """Create a new knowledge base entry."""
    kb = KnowledgeBase(
        id=str(uuid.uuid4()),
        **payload.model_dump(),
    )
    db.add(kb)
    await db.commit()
    await db.refresh(kb)
    return kb


@router.get("/knowledge", response_model=List[KnowledgeBaseOut])
async def list_knowledge_base(
    challenge_id: Optional[str] = None,
    tags: Optional[str] = None,  # Comma-separated
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """List knowledge base entries, optionally filtered by challenge or tags."""
    stmt = select(KnowledgeBase)

    if challenge_id:
        stmt = stmt.where(KnowledgeBase.challenge_id == challenge_id)

    # TODO: Implement tag filtering with JSON containment
    # if tags:
    #     tag_list = tags.split(",")
    #     stmt = stmt.where(KnowledgeBase.tags.contains(tag_list))

    stmt = stmt.order_by(KnowledgeBase.created_at.desc())
    result = await db.execute(stmt)
    entries = result.scalars().all()
    return entries


@router.get("/knowledge/{kb_id}", response_model=KnowledgeBaseOut)
async def get_knowledge_base(
    kb_id: str,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """Get a specific knowledge base entry."""
    stmt = select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    result = await db.execute(stmt)
    kb = result.scalars().first()

    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base entry not found")

    return kb


@router.patch("/knowledge/{kb_id}", response_model=KnowledgeBaseOut)
async def update_knowledge_base(
    kb_id: str,
    payload: KnowledgeBaseUpdate,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """Update a knowledge base entry."""
    stmt = select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    result = await db.execute(stmt)
    kb = result.scalars().first()

    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base entry not found")

    # Update fields
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(kb, field, value)

    await db.commit()
    await db.refresh(kb)
    return kb


@router.delete("/knowledge/{kb_id}")
async def delete_knowledge_base(
    kb_id: str,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """Delete a knowledge base entry."""
    stmt = select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    result = await db.execute(stmt)
    kb = result.scalars().first()

    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base entry not found")

    await db.delete(kb)
    await db.commit()
    return {"message": "Knowledge base entry deleted successfully"}


# ============================================================================
# Simple Challenge Verification
# ============================================================================

@router.post("/challenges/verify-prompt")
async def verify_challenge_prompt(
    payload: dict,
    _: User = Depends(require_admin),
):
    """
    Verify a Simple challenge system prompt using three-tier validation.

    Payload:
    {
      "system_prompt": "...",
      "title": "Challenge Title",
      "difficulty": "beginner|intermediate|advanced",
      "run_llm": true|false  // Optional, default true
    }
    """
    from .verification_engine import verify_system_prompt
    from .llm_router import LLMRouter

    system_prompt = payload.get("system_prompt", "")
    title = payload.get("title", "Untitled Challenge")
    difficulty = payload.get("difficulty", "beginner")
    run_llm = payload.get("run_llm", True)

    if not system_prompt:
        raise HTTPException(status_code=400, detail="system_prompt is required")

    # Initialize LLM router for Tier 2 validation
    llm_router = LLMRouter() if run_llm else None

    result = await verify_system_prompt(
        system_prompt=system_prompt,
        challenge_title=title,
        difficulty=difficulty,
        run_llm=run_llm,
        llm_router=llm_router
    )

    return result


@router.post("/challenges/{challenge_id}/test-run")
async def test_simple_challenge(
    challenge_id: str,
    payload: dict,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    """
    Run a test conversation with a Simple challenge.

    Tier 3 verification: Actually execute the challenge with a sample message
    to verify metadata is produced correctly.

    Payload:
    {
      "test_message": "Sample user message"
    }
    """
    from .variable_engine import substitute_variables
    from .prompt_injection import inject_metadata_requirements
    from .llm_router import LLMRouter
    from .schemas import LLMChatRequest
    import json as json_lib

    # Load challenge
    stmt = select(Challenge).where(Challenge.id == challenge_id)
    result = await db.execute(stmt)
    challenge = result.scalars().first()

    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    # Verify it's a Simple challenge
    if hasattr(challenge, 'challenge_type') and challenge.challenge_type != "simple":
        raise HTTPException(
            status_code=400,
            detail="Test run is only available for Simple challenges"
        )

    test_message = payload.get("test_message", "")
    if not test_message:
        raise HTTPException(status_code=400, detail="test_message is required")

    # Apply variable substitution
    try:
        system_prompt = substitute_variables(
            challenge.system_prompt,
            challenge,
            challenge.custom_variables if hasattr(challenge, 'custom_variables') else None
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Variable substitution error: {str(e)}"
        )

    # Get progress config from custom_variables if present
    progress_config = None
    if challenge.custom_variables and "progress_tracking" in challenge.custom_variables:
        progress_config = challenge.custom_variables["progress_tracking"]

    # Inject metadata requirements
    system_prompt = inject_metadata_requirements(
        system_prompt,
        challenge.title,
        challenge.xp_reward,
        challenge.passing_score,
        progress_config
    )

    # Get LLM config
    mapping_result = await db.execute(
        select(ChallengeModel).where(ChallengeModel.challenge_id == challenge_id)
    )
    mapping = mapping_result.scalars().first()

    from .config import settings
    provider = mapping.provider if mapping else settings.default_llm_provider
    model = mapping.model if mapping else settings.default_llm_model

    # Make test LLM call
    llm_router = LLMRouter()
    chat_request = LLMChatRequest(
        provider=provider,
        model=model,
        messages=[{"role": "user", "content": test_message}],
        system_prompt=system_prompt,
    )

    content = await llm_router.chat(chat_request)

    # Extract metadata
    metadata = None
    original_content = content
    if content:
        start = content.find("<metadata>")
        end = content.find("</metadata>")
        if start != -1 and end != -1:
            meta_raw = content[start + 10 : end]
            try:
                metadata = json_lib.loads(meta_raw)
            except json_lib.JSONDecodeError as e:
                metadata = {"error": f"Invalid JSON: {str(e)}", "raw": meta_raw}
            content = (content[:start] + content[end + 11 :]).strip()

    return {
        "success": metadata is not None and "error" not in metadata,
        "content": content,
        "metadata": metadata,
        "raw_response": original_content[:500] + "..." if len(original_content) > 500 else original_content,
        "metadata_found": metadata is not None,
        "system_prompt_preview": system_prompt[-1000:] if len(system_prompt) > 1000 else system_prompt,
        "provider": provider or "default",
        "model": model or "default",
        "full_response_length": len(original_content),
        "metadata_instructions_included": "<metadata>" in system_prompt
    }
