from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Software Planning Engineering Assistant"
    environment: str = "development"
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_database: str = "ai_engineering_assistant"
    ai_provider: str = "gemini"
    gemini_api_key: str | None = None
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

