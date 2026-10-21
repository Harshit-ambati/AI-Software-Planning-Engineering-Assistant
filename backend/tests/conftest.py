import pytest
from app.config import Settings
from app.main import create_app
from fastapi.testclient import TestClient


@pytest.fixture
def settings(tmp_path):
    return Settings(
        data_dir=tmp_path, ai_provider="demo", gemini_api_key="", app_access_token="", qdrant_url="", _env_file=None
    )


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as value:
        yield value
