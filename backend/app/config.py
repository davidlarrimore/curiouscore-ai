from pathlib import Path
from typing import List, Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = "sqlite+aiosqlite:///./app.db"
    secret_key: str = "change-me"
    access_token_expires_minutes: int = 60 * 24 * 7
    algorithm: str = "HS256"
    ai_gateway_url: Optional[str] = None
    ai_gateway_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_base_url: str = "https://api.openai.com"
    anthropic_api_key: Optional[str] = None
    anthropic_base_url: str = "https://api.anthropic.com"
    gemini_api_key: Optional[str] = None
    gemini_base_url: str = "https://generativelanguage.googleapis.com"
    default_llm_provider: Optional[str] = None
    default_llm_model: Optional[str] = None
    cors_origins: List[str] = ["http://localhost:8080", "http://localhost:5173"]

    @model_validator(mode="after")
    def normalize_sqlite_path(self):
        prefix = "sqlite+aiosqlite:///"
        if self.database_url.startswith(prefix):
            raw_path = self.database_url[len(prefix) :]
            # If the path is relative, anchor it to repo root and ensure the directory exists
            path_obj = Path(raw_path)
            if not path_obj.is_absolute():
                repo_root = Path(__file__).resolve().parents[2]
                path_obj = (repo_root / raw_path).resolve()
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            self.database_url = f"{prefix}{path_obj}"
        return self


settings = Settings()
