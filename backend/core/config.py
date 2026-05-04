from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://caretta:caretta@localhost:5432/carettaid"
    log_level: str = "INFO"
    upload_dir: str = "uploads"

    embedding_dim: int = 512
    similarity_threshold: float = 0.60
    top_n_matches: int = 5


@lru_cache
def get_settings() -> Settings:
    return Settings()
