from pydantic import BaseModel, Field


class APISettings(BaseModel):
    prefix: str = "/api"
    v1_prefix: str = "/v1"


class AppSettings(BaseModel):
    title: str = "CatchMe API"
    version: str = "2.0.0"
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    # Override with APP__CORS_ALLOW as a JSON array in deployed environments.
    cors_allow: list[str] = Field(default_factory=lambda: [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost",
        "http://127.0.0.1",
        "https://localhost",
        "capacitor://localhost",
        "http://localhost",
    ])
    api: APISettings = APISettings()
