from collections.abc import AsyncIterator

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://catchme:catchme@db:5432/catchme"
    secret_key: str = "change-this-secret-in-production"
    access_token_minutes: int = 60 * 24
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

# SQLAlchemy 2 async engine and session factory.
engine = create_async_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
