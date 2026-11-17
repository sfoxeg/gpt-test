from fastapi import APIRouter
from .routers import auth_router, profiles_router, me_router, chats_router
from core.realtime import router as realtime_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(profiles_router, prefix="/profiles", tags=["profiles"])
router.include_router(me_router, prefix="/me", tags=["me"])
router.include_router(chats_router, prefix="/chats", tags=["chats"])
router.include_router(realtime_router, tags=["realtime"])
