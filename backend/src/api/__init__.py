from fastapi import APIRouter
from core.settings import settings
from api.v1 import router as api_v1_router

router = APIRouter(prefix=settings.app.api.prefix, tags=["api"])
router.include_router(api_v1_router, prefix=settings.app.api.v1_prefix)
