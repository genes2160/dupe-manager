from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "dupe-manager"
    LOG_LEVEL: str = "INFO"

    SQLITE_PATH: str = "./data/dupes.db"

    USE_REDIS: bool = True
    REDIS_URL: str = "redis://localhost:6379/0"
    JOB_TTL_SECONDS: int = 60 * 60 * 24  # 24h


settings = Settings()
