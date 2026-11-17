from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict

class DBSettings(BaseSettings):
    url: str = Field(
        default="postgresql+asyncpg://catchme:catchme@db:5432/catchme",
        validation_alias=AliasChoices("DATABASE_URL", "DB__URL"),
    )
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    expire_on_commit: bool = False
    model_config = SettingsConfigDict(env_nested_delimiter="__", extra="ignore")
