from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")
    ai_provider: str = "demo"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "gemini-embedding-001"
    qdrant_url: str = ""
    data_dir: Path = ROOT / "data"
    app_access_token: str = ""
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
