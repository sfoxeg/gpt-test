import re
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import router
from core.database import dispose_database
from core.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await dispose_database()


app = FastAPI(
    title=settings.app.title,
    version=settings.app.version,
    lifespan=lifespan,
)
app.include_router(router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app.cors_allow,
    # Permit local development from localhost and private LAN IPs on any port.
    # Production frontend domains must be listed explicitly in APP__CORS_ALLOW.
    allow_origin_regex=(
        r"^https?://("
        r"localhost|127(?:\\.\\d{1,3}){3}|"
        r"10(?:\\.\\d{1,3}){3}|"
        r"192\\.168(?:\\.\\d{1,3}){2}|"
        r"172\\.(?:1[6-9]|2\\d|3[01])(?:\\.\\d{1,3}){2}"
        r")(?:\\:\\d+)?$"
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}
