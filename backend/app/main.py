from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from . import models, schemas
from .database import Base, engine, get_db
from .security import (
    create_token,
    current_user,
    hash_password,
    verify_password,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables using an async connection (development scaffold only).
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="CatchMe API",
    version="1.1.0",
    description="Climbing partner finder API",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/auth/register", status_code=201)
async def register(
    data: schemas.RegisterIn,
    db: AsyncSession = Depends(get_db),
):
    if data.date_of_birth > date.today():
        raise HTTPException(422, "Date of birth cannot be in the future")

    result = await db.execute(
        select(models.User).where(models.User.email == data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(409, "Email already registered")

    user = models.User(
        email=data.email,
        hashed_password=hash_password(data.password),
        sex=data.sex,
        date_of_birth=data.date_of_birth,
    )
    user.profile = models.Profile(
        first_name=data.first_name,
        last_name=data.last_name,
        climbing=models.Climbing(),
    )
    db.add(user)
    await db.flush()
    user_id = user.id
    await db.commit()
    return {"access_token": create_token(user_id), "token_type": "bearer"}


@app.post("/api/auth/login")
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.User).where(models.User.email == form.username)
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(401, "Incorrect email or password")
    return {"access_token": create_token(user.id), "token_type": "bearer"}


@app.get("/api/me")
async def me(user: models.User = Depends(current_user)):
    profile = user.profile
    return {
        "id": user.id,
        "email": user.email,
        "sex": user.sex,
        "date_of_birth": user.date_of_birth,
        "profile": schemas.ProfileOut.model_validate(profile),
        "climbing": {
            key: getattr(profile.climbing, key)
            for key in (
                "leading", "where_leading", "bouldering",
                "where_bouldering", "speed", "alpinism",
                "belay", "belay_description",
            )
        },
    }


@app.put("/api/me/profile")
async def update_profile(
    data: schemas.ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_user),
):
    profile = user.profile
    for key in (
        "goal", "first_name", "last_name", "description",
        "city", "height", "weight",
    ):
        setattr(profile, key, getattr(data, key))
    for key in (
        "leading", "where_leading", "bouldering",
        "where_bouldering", "speed", "alpinism",
        "belay", "belay_description",
    ):
        setattr(profile.climbing, key, getattr(data, key))
    await db.commit()
    return {"status": "updated"}


@app.get("/api/profiles")
async def search_profiles(
    looking_for: str | None = None,
    goal: int | None = Query(None, ge=0, le=3),
    age_min: int = Query(18, ge=18, le=100),
    age_max: int = Query(80, ge=18, le=100),
    city: str | None = None,
    leading: int = 0,
    where_leading: int | None = None,
    bouldering: int = 0,
    where_bouldering: int | None = None,
    belay: int | None = None,
    speed: bool | None = None,
    alpinism: bool | None = None,
    order: str = "recent",
    skip: int = 0,
    limit: int = Query(8, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_user),
):
    today = date.today()
    query = (
        select(models.Profile)
        .join(models.User)
        .join(models.Climbing)
        .options(
            selectinload(models.Profile.user),
            selectinload(models.Profile.climbing),
        )
        .where(
            models.User.is_active.is_(True),
            models.User.id != user.id,
        )
    )

    if looking_for == "male":
        query = query.where(models.User.sex.is_(False))
    if looking_for == "female":
        query = query.where(models.User.sex.is_(True))
    if goal is not None and goal < 3:
        query = query.where(models.Profile.goal == goal)
    if city:
        query = query.where(models.Profile.city.ilike(f"%{city}%"))
    if age_min > age_max:
        raise HTTPException(422, "age_min must be <= age_max")

    query = query.where(
        models.User.date_of_birth <= date(
            today.year - age_min, today.month, min(today.day, 28)
        ),
        models.User.date_of_birth >= date(
            today.year - age_max - 1, today.month, min(today.day, 28)
        ),
    )
    if leading:
        query = query.where(models.Climbing.leading >= leading)
    if where_leading is not None and where_leading < 2:
        query = query.where(
            or_(
                models.Climbing.where_leading == where_leading,
                models.Climbing.where_leading == 2,
            )
        )
    if bouldering:
        query = query.where(models.Climbing.bouldering >= bouldering)
    if where_bouldering is not None and where_bouldering < 2:
        query = query.where(
            or_(
                models.Climbing.where_bouldering == where_bouldering,
                models.Climbing.where_bouldering == 2,
            )
        )
    if belay is not None:
        query = query.where(models.Climbing.belay == belay)
    if speed:
        query = query.where(models.Climbing.speed.is_(True))
    if alpinism:
        query = query.where(models.Climbing.alpinism.is_(True))

    query = query.order_by(
        models.User.date_of_birth.asc()
        if order == "oldest"
        else models.User.date_of_birth.desc()
        if order == "youngest"
        else models.User.date_joined.desc()
    ).offset(skip).limit(limit)

    result = await db.execute(query)
    profiles = result.scalars().all()
    return [
        {
            "user_id": profile.user_id,
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "description": profile.description,
            "city": profile.city,
            "goal": profile.goal,
            "date_of_birth": profile.user.date_of_birth,
            "sex": profile.user.sex,
            "avatar": profile.avatar,
            "climbing": {
                key: getattr(profile.climbing, key)
                for key in (
                    "leading", "where_leading", "bouldering",
                    "where_bouldering", "speed", "alpinism", "belay",
                )
            },
        }
        for profile in profiles
    ]


@app.post("/api/chats", status_code=201)
async def create_chat(
    other_user_id: int,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_user),
):
    other = await db.get(models.User, other_user_id)
    if not other or other.id == user.id:
        raise HTTPException(404, "User not found")

    chat = models.Chat()
    chat.members = [
        models.ChatMember(user_id=user.id),
        models.ChatMember(user_id=other.id),
    ]
    db.add(chat)
    await db.flush()
    chat_id = chat.id
    await db.commit()
    return {"id": chat_id}


@app.get("/api/chats")
async def list_chats(
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_user),
):
    result = await db.execute(
        select(models.Chat)
        .join(models.ChatMember)
        .where(models.ChatMember.user_id == user.id)
        .options(selectinload(models.Chat.members))
    )
    chats = result.scalars().unique().all()
    return [
        {"id": chat.id, "members": [member.user_id for member in chat.members]}
        for chat in chats
    ]


@app.get("/api/chats/{chat_id}/messages")
async def list_messages(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_user),
):
    member_result = await db.execute(
        select(models.ChatMember).where(
            models.ChatMember.chat_id == chat_id,
            models.ChatMember.user_id == user.id,
        )
    )
    if not member_result.scalar_one_or_none():
        raise HTTPException(404, "Chat not found")

    result = await db.execute(
        select(models.Message)
        .where(models.Message.chat_id == chat_id)
        .order_by(models.Message.created_at)
    )
    return [
        schemas.MessageOut.model_validate(message)
        for message in result.scalars().all()
    ]


@app.post("/api/chats/{chat_id}/messages", status_code=201)
async def send_message(
    chat_id: int,
    data: schemas.MessageIn,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_user),
):
    member_result = await db.execute(
        select(models.ChatMember).where(
            models.ChatMember.chat_id == chat_id,
            models.ChatMember.user_id == user.id,
        )
    )
    if not member_result.scalar_one_or_none():
        raise HTTPException(404, "Chat not found")

    message = models.Message(
        chat_id=chat_id,
        sender_id=user.id,
        text=data.text,
    )
    db.add(message)
    await db.flush()
    await db.refresh(message)
    await db.commit()
    return schemas.MessageOut.model_validate(message)
