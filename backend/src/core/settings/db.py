from pydantic import Field
from pydantic_settings import BaseSettings

class DBSettings(BaseSettings):
    url: str = "postgresql+asyncpg://catchme:catchme@db:5432/catchme"
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    expire_on_commit: bool = False
