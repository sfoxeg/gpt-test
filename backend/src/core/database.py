from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from core.settings import settings

engine = create_async_engine(
    settings.db.url,
    echo=settings.db.echo,
    echo_pool=settings.db.echo_pool,
    pool_pre_ping=True,
    pool_size=settings.db.pool_size,
    max_overflow=settings.db.max_overflow,
)
new_session = async_sessionmaker(
    engine,
    expire_on_commit=settings.db.expire_on_commit,
    autoflush=False,
)

async def dispose_database() -> None:
    await engine.dispose()
