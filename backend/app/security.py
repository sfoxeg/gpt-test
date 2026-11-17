from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .database import get_db, settings
from .models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_token(user_id: int) -> str:
    expires = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_minutes
    )
    return jwt.encode(
        {"sub": str(user_id), "exp": expires},
        settings.secret_key,
        algorithm="HS256",
    )


async def current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=["HS256"]
        )
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise error

    result = await db.execute(
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.profile).selectinload("climbing")
        )
    )
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise error
    return user
