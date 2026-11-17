from datetime import date
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from core.database import new_session
from core.models import UsersOrm, ProfilesOrm, ClimbingOrm
from core.schemas import SUserReg, SUserAuth
from core.secure import hash_password, verify_password, create_access_token

class AuthRepository:
    @classmethod
    async def register(cls, data: SUserReg) -> dict:
        if data.date_of_birth > date.today():
            raise HTTPException(422, "Date of birth cannot be in the future")
        async with new_session() as session:
            exists = await session.scalar(select(UsersOrm.id).where(UsersOrm.email == data.email))
            if exists:
                raise HTTPException(409, "Email already registered")
            user = UsersOrm(
                email=data.email, hashed_password=hash_password(data.password),
                sex=data.sex, date_of_birth=data.date_of_birth,
                profile=ProfilesOrm(
                    first_name=data.first_name, last_name=data.last_name,
                    climbing=ClimbingOrm(),
                ),
            )
            session.add(user)
            await session.flush()
            user_id = user.id
            await session.commit()
            return {"access_token": create_access_token(user_id), "token_type": "bearer"}

    @classmethod
    async def login(cls, data: SUserAuth) -> dict:
        async with new_session() as session:
            user = await session.scalar(select(UsersOrm).where(UsersOrm.email == data.email))
            if not user or not verify_password(data.password, user.hashed_password):
                raise HTTPException(401, "Incorrect email or password")
            return {"access_token": create_access_token(user.id), "token_type": "bearer"}

    @classmethod
    async def get_user_by_id(cls, user_id: int) -> UsersOrm | None:
        async with new_session() as session:
            result = await session.execute(
                select(UsersOrm).where(UsersOrm.id == user_id).options(
                    selectinload(UsersOrm.profile).selectinload(ProfilesOrm.climbing)
                )
            )
            return result.scalar_one_or_none()
