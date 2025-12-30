import json
from datetime import datetime
from typing import List, AsyncIterator
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from .config import settings
from .database import Base, engine, get_session
from .models import User, Badge, UserBadge, Challenge, UserProgress, ChallengeModel
from .schemas import (
    UserCreate,
    UserLogin,
    UserBase,
    Token,
    BadgeOut,
    UserBadgeOut,
    ChallengeOut,
    ProgressOut,
    ProgressUpdate,
    ProfileUpdate,
    ChatRequest,
    ChatResponse,
    LLMProvider,
    LLMModelOut,
    LLMCompletionRequest,
    LLMChatRequest,
)
from .auth import get_password_hash, verify_password, create_access_token
from .deps import get_current_user, require_admin
from .llm_router import llm_router
from .schemas import ChatMessage
from .session_endpoints import router as session_router
from .admin_routes import router as admin_router


app = FastAPI(title="CuriousCore API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include session router for Game Master architecture
app.include_router(session_router)

# Include admin router for admin panel management
app.include_router(admin_router)


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _seed_initial_data()


def user_to_schema(user: User) -> UserBase:
    return UserBase(
        id=user.id,
        email=user.email,
        username=user.username,
        avatar_url=user.avatar_url,
        role=user.role,
        xp=user.xp,
        level=user.level,
        created_at=user.created_at,
    )


@app.post("/auth/register", response_model=Token)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_session)):
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalars().first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    admin_exists = await db.execute(select(User.id).where(User.role == "admin"))
    should_set_admin = admin_exists.scalars().first() is None

    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        username=payload.username or payload.email.split("@")[0],
        role="admin" if should_set_admin else "user",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token({"sub": user.id})
    return Token(access_token=token)


@app.post("/auth/login", response_model=Token)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalars().first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")
    token = create_access_token({"sub": user.id})
    return Token(access_token=token)


@app.get("/auth/me", response_model=UserBase)
async def me(current_user: User = Depends(get_current_user)):
    return user_to_schema(current_user)


@app.get("/badges", response_model=List[BadgeOut])
async def list_badges(db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Badge))
    return result.scalars().all()


@app.get("/badges/me", response_model=List[UserBadgeOut])
async def my_badges(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(UserBadge)
        .where(UserBadge.user_id == current_user.id)
        .join(Badge)
    )
    user_badges = result.scalars().unique().all()
    return user_badges


@app.get("/challenges", response_model=List[ChallengeOut])
async def list_challenges(db: AsyncSession = Depends(get_session)):
    stmt = select(Challenge).options(selectinload(Challenge.llm_config)).where(Challenge.is_active == True)  # noqa: E712
    result = await db.execute(stmt)
    return result.scalars().all()


@app.get("/challenges/{challenge_id}", response_model=ChallengeOut)
async def get_challenge(challenge_id: str, db: AsyncSession = Depends(get_session)):
    stmt = select(Challenge).options(selectinload(Challenge.llm_config)).where(Challenge.id == challenge_id)
    result = await db.execute(stmt)
    challenge = result.scalars().first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return challenge


@app.get("/profile", response_model=UserBase)
async def get_profile(current_user: User = Depends(get_current_user)):
    return user_to_schema(current_user)


@app.patch("/profile", response_model=UserBase)
async def update_profile(payload: ProfileUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    if payload.username is not None:
        current_user.username = payload.username
    if payload.avatar_url is not None:
        current_user.avatar_url = payload.avatar_url
    if payload.xp is not None:
        current_user.xp = payload.xp
    if payload.level is not None:
        current_user.level = payload.level

    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return user_to_schema(current_user)


@app.get("/progress", response_model=List[ProgressOut])
async def list_progress(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(UserProgress).where(UserProgress.user_id == current_user.id))
    return result.scalars().all()


@app.get("/progress/{challenge_id}", response_model=ProgressOut | None)
async def get_progress(challenge_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(UserProgress).where(
            UserProgress.user_id == current_user.id,
            UserProgress.challenge_id == challenge_id,
        )
    )
    return result.scalars().first()


@app.post("/progress/{challenge_id}/start", response_model=ProgressOut)
async def start_progress(challenge_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    existing = await db.execute(
        select(UserProgress).where(
            UserProgress.user_id == current_user.id,
            UserProgress.challenge_id == challenge_id,
        )
    )
    progress = existing.scalars().first()
    if not progress:
        progress = UserProgress(
            user_id=current_user.id,
            challenge_id=challenge_id,
            status="in_progress",
            started_at=datetime.utcnow(),
            messages=[],
        )
    progress.status = "in_progress"
    progress.started_at = datetime.utcnow()
    progress.completed_at = None
    db.add(progress)
    await db.commit()
    await db.refresh(progress)
    return progress


@app.post("/progress/{challenge_id}/reset", response_model=ProgressOut)
async def reset_progress(challenge_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    existing = await db.execute(
        select(UserProgress).where(
            UserProgress.user_id == current_user.id,
            UserProgress.challenge_id == challenge_id,
        )
    )
    progress = existing.scalars().first()
    if not progress:
        progress = UserProgress(
            user_id=current_user.id,
            challenge_id=challenge_id,
            status="not_started",
            started_at=None,
            messages=[],
            progress_percent=0,
            score=0,
            current_phase=1,
            mistakes_count=0,
        )
    else:
        progress.status = "not_started"
        progress.messages = []
        progress.progress_percent = 0
        progress.score = 0
        progress.current_phase = 1
        progress.mistakes_count = 0
        progress.started_at = None
        progress.completed_at = None

    db.add(progress)
    await db.commit()
    await db.refresh(progress)
    return progress


def _serialize_messages(messages: List[ChatMessage] | None) -> List[dict] | None:
    if messages is None:
        return None
    serialized = []
    for m in messages:
        serialized.append(
            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp.isoformat() if isinstance(m.timestamp, datetime) else m.timestamp,
                "metadata": m.metadata.model_dump() if m.metadata else None,
            }
        )
    return serialized


@app.patch("/progress/{challenge_id}", response_model=ProgressOut)
async def update_progress(
    challenge_id: str,
    payload: ProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    result = await db.execute(
        select(UserProgress).where(
            UserProgress.user_id == current_user.id,
            UserProgress.challenge_id == challenge_id,
        )
    )
    progress = result.scalars().first()
    if not progress:
        raise HTTPException(status_code=404, detail="Progress not found")

    data = payload.model_dump(exclude_unset=True)
    if "messages" in data:
        data["messages"] = _serialize_messages(payload.messages)

    for field, value in data.items():
        setattr(progress, field, value)

    db.add(progress)
    await db.commit()
    await db.refresh(progress)
    return progress


@app.get("/llm/models", response_model=List[LLMModelOut])
async def list_llm_models(provider: LLMProvider, _: User = Depends(require_admin)):
    return await llm_router.list_models(provider)


@app.post("/llm/completions")
async def llm_completion(payload: LLMCompletionRequest, _: User = Depends(require_admin)):
    content = await llm_router.completion(payload)
    return {"content": content}


@app.post("/llm/chat")
async def llm_chat(payload: LLMChatRequest, _: User = Depends(require_admin)):
    content = await llm_router.chat(payload)
    return {"content": content}


# NOTE: Old admin endpoints moved to admin_routes.py
# These are commented out to avoid conflicts with the new unified admin API

# @app.get("/admin/challenges", response_model=List[ChallengeOut])
# async def list_all_challenges(_: User = Depends(require_admin), db: AsyncSession = Depends(get_session)):
#     result = await db.execute(select(Challenge).options(selectinload(Challenge.llm_config)))
#     return result.scalars().all()


# @app.patch("/admin/challenges/{challenge_id}/activation", response_model=ChallengeOut)
# async def update_challenge_activation(
#     challenge_id: str,
#     payload: ChallengeActivationUpdate,
#     _: User = Depends(require_admin),
#     db: AsyncSession = Depends(get_session),
# ):
#     result = await db.execute(
#         select(Challenge).options(selectinload(Challenge.llm_config)).where(Challenge.id == challenge_id)
#     )
#     challenge = result.scalars().first()
#     if not challenge:
#         raise HTTPException(status_code=404, detail="Challenge not found")
#     challenge.is_active = payload.is_active
#     db.add(challenge)
#     await db.commit()
#     await db.refresh(challenge)
#     return challenge


# @app.patch("/admin/challenges/{challenge_id}/prompt", response_model=ChallengeOut)
# async def update_challenge_prompt(
#     challenge_id: str,
#     payload: ChallengePromptUpdate,
#     _: User = Depends(require_admin),
#     db: AsyncSession = Depends(get_session),
# ):
#     result = await db.execute(
#         select(Challenge).options(selectinload(Challenge.llm_config)).where(Challenge.id == challenge_id)
#     )
#     challenge = result.scalars().first()
#     if not challenge:
#         raise HTTPException(status_code=404, detail="Challenge not found")
#     challenge.system_prompt = payload.system_prompt
#     db.add(challenge)
#     await db.commit()
#     await db.refresh(challenge)
#     return challenge


@app.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    if not payload.challengeId:
        raise HTTPException(status_code=400, detail="challengeId is required")

    challenge_result = await db.execute(
        select(Challenge).options(selectinload(Challenge.llm_config)).where(Challenge.id == payload.challengeId)
    )
    challenge = challenge_result.scalars().first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    # Block advanced challenges from using /chat endpoint
    if hasattr(challenge, 'challenge_type') and challenge.challenge_type == "advanced":
        raise HTTPException(
            status_code=400,
            detail="This is an Advanced challenge. Please use the /sessions API instead."
        )

    mapping_result = await db.execute(select(ChallengeModel).where(ChallengeModel.challenge_id == payload.challengeId))
    mapping = mapping_result.scalars().first()

    provider = mapping.provider if mapping else settings.default_llm_provider
    model = mapping.model if mapping else settings.default_llm_model

    if not provider or not model:
        raise HTTPException(status_code=400, detail="No model configured for this challenge")

    # For Simple challenges, apply variable substitution and metadata injection
    system_prompt = payload.systemPrompt or challenge.system_prompt

    if hasattr(challenge, 'challenge_type') and challenge.challenge_type == "simple":
        from .variable_engine import substitute_variables
        from .prompt_injection import inject_metadata_requirements

        try:
            # Apply variable substitution
            system_prompt = substitute_variables(
                system_prompt,
                challenge,
                challenge.custom_variables if hasattr(challenge, 'custom_variables') else None
            )

            # Inject metadata requirements
            system_prompt = inject_metadata_requirements(
                system_prompt,
                challenge.title,
                challenge.xp_reward,
                challenge.passing_score
            )
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Variable substitution error: {str(e)}"
            )

    messages_payload = [{"role": m.role, "content": m.content} for m in payload.messages]
    chat_request = LLMChatRequest(
        provider=provider,
        model=model,
        messages=messages_payload,
        system_prompt=system_prompt,
    )

    content = await llm_router.chat(chat_request)

    metadata = None
    if content:
        start = content.find("<metadata>")
        end = content.find("</metadata>")
        if start != -1 and end != -1:
            meta_raw = content[start + 10 : end]
            try:
                metadata = json.loads(meta_raw)
            except json.JSONDecodeError:
                metadata = None
            content = (content[:start] + content[end + 11 :]).strip()

    return ChatResponse(content=content, metadata=metadata)


async def _seed_initial_data():
    async with engine.begin() as conn:
        async with AsyncSession(bind=conn) as session:
            badge_count = (await session.execute(select(Badge))).scalars().first()
            if not badge_count:
                badges = [
                    Badge(name="First Steps", description="Complete your first challenge", icon="trophy", badge_type="milestone", xp_reward=50),
                    Badge(name="Quick Learner", description="Complete 5 challenges", icon="zap", badge_type="milestone", xp_reward=100),
                Badge(name="AI Explorer", description="Complete 10 challenges", icon="compass", badge_type="milestone", xp_reward=200),
            ]
            session.add_all(badges)
        challenge_count = (await session.execute(select(Challenge))).scalars().first()
        if not challenge_count:
            challenges = [
                Challenge(
                    title="Introduction to Large Language Models",
                    description="Learn the fundamentals of LLMs, including transformers, tokenization, and how modern AI models understand and generate text.",
                    tags=["Generative AI", "NLP"],
                    difficulty="beginner",
                    system_prompt="You are an expert AI instructor teaching about Large Language Models...",
                    estimated_time_minutes=25,
                    xp_reward=150,
                    passing_score=70,
                    help_resources=[
                        {"title": "Transformer Architecture", "url": "https://arxiv.org/abs/1706.03762"},
                        {"title": "OpenAI GPT Guide", "url": "https://platform.openai.com/docs"},
                    ],
                ),
                Challenge(
                    title="Prompt Engineering Fundamentals",
                    description="Master the art of crafting effective prompts to get the best results from AI models.",
                    tags=["Prompt Engineering", "Generative AI"],
                    difficulty="beginner",
                    system_prompt="You are a prompt engineering expert...",
                    estimated_time_minutes=30,
                    xp_reward=175,
                    passing_score=70,
                    help_resources=[
                        {"title": "OpenAI Prompt Engineering Guide", "url": "https://platform.openai.com/docs/guides/prompt-engineering"},
                    ],
                ),
            ]
            session.add_all(challenges)
        await session.commit()
