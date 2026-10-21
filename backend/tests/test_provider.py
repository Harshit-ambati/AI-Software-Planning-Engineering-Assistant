from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from app.config import Settings
from app.demo import fixture
from app.provider import Provider
from google.genai import errors


def configured():
    provider = Provider(Settings(ai_provider="gemini", gemini_api_key="", _env_file=None))
    provider.client = SimpleNamespace(models=SimpleNamespace(generate_content=Mock()))
    return provider


def response(content):
    import json

    return SimpleNamespace(
        text=json.dumps(content), usage_metadata=SimpleNamespace(prompt_token_count=50, candidates_token_count=20)
    )


def test_invalid_model_output_is_retried_and_accounted():
    provider = configured()
    provider.client.models.generate_content.side_effect = [
        response({"bad": "shape"}),
        response(fixture("requirements")),
    ]
    artifact, meta = provider.generate("requirements", {"brief": "Synthetic test brief"})
    assert artifact["functional"][0]["id"] == "FR-1"
    assert meta["attempts"] == 2 and meta["input_tokens"] == 100 and meta["output_tokens"] == 40
    assert provider.client.models.generate_content.call_args.kwargs["config"].response_json_schema


def test_invalid_outputs_fail_without_demo_fallback():
    provider = configured()
    provider.client.models.generate_content.return_value = response({"bad": "shape"})
    with pytest.raises(RuntimeError, match="after 3 attempts"):
        provider.generate("requirements", {})
    assert provider.client.models.generate_content.call_count == 3


def test_permanent_provider_failure_does_not_leak_error_body():
    provider = configured()
    provider.client.models.generate_content.side_effect = errors.ClientError(
        403, {"message": "sensitive upstream body"}
    )
    with pytest.raises(RuntimeError) as caught:
        provider.generate("requirements", {})
    assert "sensitive" not in str(caught.value)
    assert provider.client.models.generate_content.call_count == 1


def test_transient_failure_has_bounded_retry(monkeypatch):
    provider = configured()
    monkeypatch.setattr("app.provider.time.sleep", lambda _: None)
    provider.client.models.generate_content.side_effect = [
        errors.ServerError(503, {"message": "retry"}),
        response(fixture("apis")),
    ]
    artifact, meta = provider.generate("apis", {})
    assert artifact["endpoints"] and meta["attempts"] == 2
