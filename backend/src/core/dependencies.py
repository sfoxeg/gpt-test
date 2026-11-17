from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from core.database import new_session
from core.models import UsersOrm, ProfilesOrm
from core.settings import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UsersOrm:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise credentials_error
    async with new_session() as session:
        result = await session.execute(select(UsersOrm).where(
            UsersOrm.id == user_id, UsersOrm.is_active.is_(True)
        ).options(selectinload(UsersOrm.profile).selectinload(ProfilesOrm.climbing)))
        user = result.scalar_one_or_none()
        if user is None:
            raise credentials_error
        # Detach safe loaded graph before session close.
        return user

async def get_current_user_id(user: Annotated[UsersOrm, Depends(get_current_user)]) -> int:
    return user.id
