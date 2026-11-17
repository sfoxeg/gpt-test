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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}
