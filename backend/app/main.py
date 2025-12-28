import json
from datetime import datetime
from typing import List, AsyncIterator
import httpx
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .config import settings
from .database import Base, engine, get_session
from .models import User, Badge, UserBadge, Challenge, UserProgress
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
)
from .auth import get_password_hash, verify_password, create_access_token
from .deps import get_current_user


app = FastAPI(title="CuriousCore API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        username=payload.username or payload.email.split("@")[0],
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
    result = await db.execute(select(Challenge).where(Challenge.is_active == True))  # noqa: E712
    return result.scalars().all()


@app.get("/challenges/{challenge_id}", response_model=ChallengeOut)
async def get_challenge(challenge_id: str, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Challenge).where(Challenge.id == challenge_id))
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
    db.add(progress)
    await db.commit()
    await db.refresh(progress)
    return progress


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

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(progress, field, value)

    db.add(progress)
    await db.commit()
    await db.refresh(progress)
    return progress


@app.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, current_user: User = Depends(get_current_user)):
    if not settings.ai_gateway_url or not settings.ai_gateway_api_key:
        raise HTTPException(status_code=500, detail="AI gateway not configured")

    messages_payload = [
        {"role": m.role, "content": m.content} for m in payload.messages
    ]
    request_body = {
        "model": "google/gemini-2.5-flash",
        "messages": [{"role": "system", "content": payload.systemPrompt}, *messages_payload],
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            settings.ai_gateway_url,
            headers={
                "Authorization": f"Bearer {settings.ai_gateway_api_key}",
                "Content-Type": "application/json",
            },
            json=request_body,
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="AI gateway error")

    data = resp.json()
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

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
