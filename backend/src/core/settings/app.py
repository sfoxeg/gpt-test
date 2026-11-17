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
    # Capacitor origins for native WebViews plus local web development.
    cors_allow: list[str] = Field(default_factory=lambda: [
        "http://localhost:5173",
        "http://localhost",
        "https://localhost",
        "capacitor://localhost",
    ])
    api: APISettings = APISettings()
