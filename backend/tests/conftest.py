import os
from uuid import uuid4

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text
from core.models import Base
import core.repositories.auth as auth_repo
import core.repositories.profiles as profiles_repo
import core.repositories.chats as chats_repo
import core.realtime as realtime
import core.dependencies as dependencies
from core.database import new_session as production_session
from main import app

@pytest_asyncio.fixture
async def test_db():
    database_url = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    is_postgres = database_url.startswith("postgresql")
    schema = f"test_{uuid4().hex}" if is_postgres else None

    if is_postgres:
        admin_engine = create_async_engine(database_url)
        async with admin_engine.begin() as connection:
            await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        await admin_engine.dispose()
        engine = create_async_engine(
            database_url,
            connect_args={"server_settings": {"search_path": schema}},
        )
    else:
        engine = create_async_engine(database_url)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    for module in (auth_repo, profiles_repo, chats_repo, dependencies, realtime):
        module.new_session = factory

    try:
        yield factory
    finally:
        for module in (auth_repo, profiles_repo, chats_repo, dependencies):
            module.new_session = production_session
        await engine.dispose()
        if is_postgres:
            admin_engine = create_async_engine(database_url)
            async with admin_engine.begin() as connection:
                await connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
            await admin_engine.dispose()

@pytest_asyncio.fixture
async def client(test_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
