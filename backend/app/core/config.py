from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://localhost:5432/hireai"
    secret_key: str = Field(min_length=32)
    environment: str = "development"
    cookie_secure: bool = False
    frontend_origin: str = "http://localhost:5173"
    token_minutes: int = 60
    storage_dir: str = "storage/resumes"
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    embeddings_enabled: bool = True
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_cache_dir: str = "storage/model-cache/hub"
    skill_weight: float = Field(0.5, ge=0, le=1)
    semantic_weight: float = Field(0.3, ge=0, le=1)
    experience_weight: float = Field(0.1, ge=0, le=1)
    location_weight: float = Field(0.1, ge=0, le=1)


@lru_cache
def settings():
    config = Settings()
    if config.environment == "production" and not config.cookie_secure:
        raise ValueError("Production requires COOKIE_SECURE=true and HTTPS")
    return config
