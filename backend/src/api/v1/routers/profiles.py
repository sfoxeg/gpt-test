from typing import Annotated
from fastapi import APIRouter, Depends, Query
from core.repositories import ProfilesRepository
from core.schemas import SProfileUpdate
from core.dependencies import get_current_user_id

router = APIRouter()

@router.get("")
async def search_profiles(
    user_id: Annotated[int, Depends(get_current_user_id)],
    looking_for: str | None = None, goal: int | None = Query(None, ge=0, le=3),
    age_min: int = Query(18, ge=18, le=100), age_max: int = Query(80, ge=18, le=100),
    city: str | None = None, leading: int = 0, where_leading: int | None = None,
    bouldering: int = 0, where_bouldering: int | None = None, belay: int | None = None,
    speed: bool | None = None, alpinism: bool | None = None, order: str = "recent",
    skip: int = Query(0, ge=0), limit: int = Query(8, ge=1, le=50),
):
    return await ProfilesRepository.search(
        user_id=user_id, looking_for=looking_for, goal=goal, age_min=age_min, age_max=age_max,
        city=city, leading=leading, where_leading=where_leading, bouldering=bouldering,
        where_bouldering=where_bouldering, belay=belay, speed=speed, alpinism=alpinism,
        order=order, skip=skip, limit=limit,
    )

@router.put("/me")
async def update_my_profile(
    data: SProfileUpdate,
    user_id: Annotated[int, Depends(get_current_user_id)],
):
    await ProfilesRepository.update(user_id, data)
    return {"status": "updated"}
