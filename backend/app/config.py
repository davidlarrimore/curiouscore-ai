from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./app.db"
    secret_key: str = "change-me"
    access_token_expires_minutes: int = 60 * 24 * 7
    algorithm: str = "HS256"
    ai_gateway_url: str | None = None
    ai_gateway_api_key: str | None = None
    cors_origins: List[str] = ["http://localhost:8080", "http://localhost:5173"]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
