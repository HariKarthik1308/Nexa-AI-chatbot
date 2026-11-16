from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "NexaAI"
    API_V1_STR: str = "/api/v1"
    LOG_LEVEL: str = "INFO"

    # Security
    SECRET_KEY: str = "insecure_dev_secret_key_change_in_production_32_chars_min"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALGORITHM: str = "HS256"

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Database
    # Default to local SQLite async for testing / development without needing external postgres daemon,
    # or override with postgresql+asyncpg://user:pass@localhost:5432/nexa_ai
    DATABASE_URL: str = "sqlite+aiosqlite:///./nexa_ai.db"

    # Redis (Optional in Phase 2)
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM Settings (Server-side secrets)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
