import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from core.models import Base
import core.repositories.auth as auth_repo
import core.repositories.profiles as profiles_repo
import core.repositories.chats as chats_repo
import core.dependencies as dependencies
from core.database import new_session as production_session
from main import app

@pytest_asyncio.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    for module in (auth_repo, profiles_repo, chats_repo, dependencies):
        module.new_session = factory
    yield factory
    for module in (auth_repo, profiles_repo, chats_repo, dependencies):
        module.new_session = production_session
    await engine.dispose()

@pytest_asyncio.fixture
async def client(test_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
