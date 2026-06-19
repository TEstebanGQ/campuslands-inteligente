from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    openai_api_key: Optional[str] = "mock-key"
    google_api_key: Optional[str] = None
    orchestrator_model: str = "gpt-4o-mini"
    google_orchestrator_model: str = "gemini-2.5-flash"
    fiftyone_port: int = 5151
    fiftyone_host: str = "127.0.0.1"
    database_url: str = "sqlite+aiosqlite:///:memory:"

@lru_cache
def get_settings() -> Settings:
    return Settings()
