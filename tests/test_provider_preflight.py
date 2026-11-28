from __future__ import annotations

import json

import pytest

from src.config import Settings
from src.provider_preflight import check_provider_prerequisites, main


def _settings(model: str, provider: str = "litellm") -> Settings:
    return Settings.from_environment(
        {"LLM_PROVIDER": provider, "LLM_MODEL": model}
    )


@pytest.mark.parametrize(
    ("model", "key_name"),
    [
        ("openrouter/vendor/model", "OPENROUTER_API_KEY"),
        ("nvidia_nim/vendor/model", "NVIDIA_NIM_API_KEY"),
    ],
)
def test_preflight_checks_only_the_selected_provider_key(model, key_name):
    missing = check_provider_prerequisites(_settings(model), {})
    assert missing.configuration_complete is False
    assert missing.credential_variable == key_name
    assert missing.issues == (f"{key_name} is required",)

    secret = "synthetic-test-secret"
    complete = check_provider_prerequisites(_settings(model), {key_name: secret})
    assert complete.configuration_complete is True
    assert complete.issues == ()
    assert complete.network_call_performed is False
    assert complete.runtime_provider_enabled is False
    assert secret not in repr(complete)


@pytest.mark.parametrize(
    "model",
    ["", "unprefixed", "openrouter/", "openrouter//model", "nvidia_nim/", "unknown/vendor/model", "openrouter/a b"],
)
def test_preflight_rejects_missing_or_unsupported_model(model):
    result = check_provider_prerequisites(_settings(model), {})
    assert result.configuration_complete is False
    assert result.credential_variable is None
    assert any("LLM_MODEL" in issue for issue in result.issues)


def test_mock_provider_cannot_pass_real_provider_preflight():
    result = check_provider_prerequisites(_settings("openrouter/vendor/model", "mock"), {
        "OPENROUTER_API_KEY": "synthetic-test-secret"
    })
    assert result.configuration_complete is False
    assert any("LLM_PROVIDER" in issue for issue in result.issues)


def test_preflight_rejects_unverified_nim_output_controls():
    settings = Settings.from_environment({
        "LLM_PROVIDER": "litellm",
        "LLM_MODEL": "nvidia_nim/vendor/model",
        "LLM_REASONING_EFFORT": "none",
        "LLM_RESPONSE_FORMAT": "json_object",
    })
    result = check_provider_prerequisites(settings, {"NVIDIA_NIM_API_KEY": "synthetic-test-secret"})
    assert result.configuration_complete is False
    assert any("only for openrouter" in issue for issue in result.issues)


def test_cli_output_never_contains_credential(monkeypatch, capsys):
    secret = "synthetic-test-secret"
    monkeypatch.setenv("APP_PROFILE", "development")
    monkeypatch.setenv("LLM_PROVIDER", "litellm")
    monkeypatch.setenv("LLM_MODEL", "openrouter/vendor/model")
    monkeypatch.setenv("OPENROUTER_API_KEY", secret)
    assert main() == 0
    output = capsys.readouterr().out
    assert secret not in output
    assert json.loads(output)["configuration_complete"] is True
    assert json.loads(output)["runtime_provider_enabled"] is False
