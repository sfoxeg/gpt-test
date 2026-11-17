from datetime import date
from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload
from core.database import new_session
from core.models import UsersOrm, ProfilesOrm, ClimbingOrm
from core.schemas import SProfileUpdate

class ProfilesRepository:
    @classmethod
    async def update(cls, user_id: int, data: SProfileUpdate) -> None:
        async with new_session() as session:
            profile = await session.get(ProfilesOrm, user_id, options=[selectinload(ProfilesOrm.climbing)])
            if profile is None:
                raise HTTPException(404, "Profile not found")
            values = data.model_dump()
            for key in ("goal", "first_name", "last_name", "description", "city", "height", "weight"):
                setattr(profile, key, values[key])
            for key in ("leading", "where_leading", "bouldering", "where_bouldering", "speed", "alpinism", "belay", "belay_description"):
                setattr(profile.climbing, key, values[key])
            await session.commit()

    @classmethod
    async def search(cls, *, user_id: int, looking_for: str | None, goal: int | None,
        age_min: int, age_max: int, city: str | None, leading: int,
        where_leading: int | None, bouldering: int, where_bouldering: int | None,
        belay: int | None, speed: bool | None, alpinism: bool | None,
        order: str, skip: int, limit: int) -> list[dict]:
        if age_min > age_max:
            raise HTTPException(422, "age_min must be <= age_max")
        today = date.today()
        query = select(ProfilesOrm).join(UsersOrm).join(ClimbingOrm).options(
            selectinload(ProfilesOrm.user), selectinload(ProfilesOrm.climbing)
        ).where(UsersOrm.is_active.is_(True), UsersOrm.id != user_id)
        if looking_for == "male":
            query = query.where(UsersOrm.sex.is_(False))
        elif looking_for == "female":
            query = query.where(UsersOrm.sex.is_(True))
        if goal is not None and goal < 3:
            query = query.where(ProfilesOrm.goal == goal)
        if city:
            query = query.where(ProfilesOrm.city.ilike(f"%{city}%"))
        query = query.where(
            UsersOrm.date_of_birth <= date(today.year-age_min, today.month, min(today.day,28)),
            UsersOrm.date_of_birth >= date(today.year-age_max-1, today.month, min(today.day,28)),
        )
        if leading: query = query.where(ClimbingOrm.leading >= leading)
        if where_leading is not None and where_leading < 2:
            query = query.where(or_(ClimbingOrm.where_leading == where_leading, ClimbingOrm.where_leading == 2))
        if bouldering: query = query.where(ClimbingOrm.bouldering >= bouldering)
        if where_bouldering is not None and where_bouldering < 2:
            query = query.where(or_(ClimbingOrm.where_bouldering == where_bouldering, ClimbingOrm.where_bouldering == 2))
        if belay is not None: query = query.where(ClimbingOrm.belay == belay)
        if speed: query = query.where(ClimbingOrm.speed.is_(True))
        if alpinism: query = query.where(ClimbingOrm.alpinism.is_(True))
        sort_column = UsersOrm.date_of_birth.asc() if order == "oldest" else UsersOrm.date_of_birth.desc() if order == "youngest" else UsersOrm.date_joined.desc()
        async with new_session() as session:
            result = await session.execute(query.order_by(sort_column).offset(skip).limit(limit))
            return [{
                "user_id": p.user_id, "first_name": p.first_name, "last_name": p.last_name,
                "description": p.description, "city": p.city, "goal": p.goal,
                "date_of_birth": p.user.date_of_birth, "sex": p.user.sex, "avatar": p.avatar,
                "climbing": {k: getattr(p.climbing, k) for k in (
                    "leading", "where_leading", "bouldering", "where_bouldering",
                    "speed", "alpinism", "belay",
                )},
            } for p in result.scalars().all()]
