from pydantic_settings import BaseSettings, SettingsConfigDict
from .app import AppSettings
from .db import DBSettings

class Settings(BaseSettings):
    app: AppSettings = AppSettings()
    db: DBSettings = DBSettings()
    secret_key: str = "change-this-secret-in-production"
    access_token_minutes: int = 1440
    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__", extra="ignore")

settings = Settings()
