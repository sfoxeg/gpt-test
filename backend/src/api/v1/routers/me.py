from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from core.dependencies import get_current_user
from core.models import UsersOrm
from core.schemas import SProfileOut

router = APIRouter()

@router.get("")
async def get_me(user: Annotated[UsersOrm, Depends(get_current_user)]):
    profile = user.profile
    if profile is None or profile.climbing is None:
        raise HTTPException(404, "Profile not found")
    return {
        "id": user.id, "email": user.email, "sex": user.sex,
        "date_of_birth": user.date_of_birth,
        "profile": SProfileOut.model_validate(profile),
        "climbing": {k: getattr(profile.climbing, k) for k in (
            "leading", "where_leading", "bouldering", "where_bouldering",
            "speed", "alpinism", "belay", "belay_description",
        )},
    }
