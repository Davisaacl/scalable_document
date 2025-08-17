### Environment variables
# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "doc-pipeline"
    ENV: str = "dev"
    LOG_LEVEL: str = "INFO"
    DATA_DIR: str = "./data"
    INDEX_DIR: str = "./data/index"
    DB_PATH: str = "./data/meta.duckdb"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    ENABLE_RQ: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

@lru_cache()
def get_settings() -> Settings:
    return Settings()
