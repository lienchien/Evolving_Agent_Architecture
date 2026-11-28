from __future__ import annotations

from decimal import Decimal

import pytest

from src.config import Settings
from src.main import Container


def test_default_settings_preserve_phase1_local_runtime():
    config = Settings.from_environment({})
    assert config.profile == "development"
    assert config.llm_provider == "mock"
    assert config.llm_request_timeout_seconds == 30.0
    assert config.llm_max_output_tokens == 2048
    assert config.llm_reasoning_effort is None
    assert config.llm_response_format is None
    assert config.database_path == "capability_library.db"
    assert config.report_directory == "capability_library"
    assert config.sandbox_backend == "subprocess"
    assert config.sandbox_timeout_seconds == 5.0
    assert config.retry_hard_max == 3
    assert config.enable_code_builder is False
    config.validate_available_adapters()


def test_test_profile_and_runtime_limits_are_loaded_and_wired(tmp_path):
    config = Settings.from_environment(
        {
            "APP_PROFILE": "test",
            "DATABASE_URL": str(tmp_path / "configured.db"),
            "REPORT_DIRECTORY": str(tmp_path / "reports"),
            "SANDBOX_TIMEOUT_SECONDS": "2.5",
            "RETRY_HARD_MAX": "1",
            "RETRY_BACKOFF_MS": "50",
        }
    )
    container = Container(runtime_settings=config)
    assert (tmp_path / "configured.db").exists()
    assert container.runtime_settings is config
    assert container.testing_service._report_directory == tmp_path / "reports"
    assert container.execution_service._sandbox._timeout == 2.5
    assert container.retry_policy._hard_max_retries == 1
    assert container.retry_policy._base_backoff_ms == 50


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("APP_PROFILE", "production"),
        ("LLM_PROVIDER", "unknown"),
        ("SANDBOX_BACKEND", "none"),
        ("DATABASE_URL", ""),
        ("REPORT_DIRECTORY", ""),
        ("SANDBOX_TIMEOUT_SECONDS", "0"),
        ("SANDBOX_TIMEOUT_SECONDS", "nan"),
        ("LLM_REQUEST_TIMEOUT_SECONDS", "0"),
        ("LLM_MAX_OUTPUT_TOKENS", "0"),
        ("LLM_MAX_OUTPUT_TOKENS", "8193"),
        ("LLM_REASONING_EFFORT", "off"),
        ("LLM_RESPONSE_FORMAT", "json_schema"),
        ("RETRY_HARD_MAX", "4"),
        ("RETRY_BACKOFF_MS", "-1"),
        ("BUILDER_MAX_TOKENS", "nope"),
        ("BUILDER_MAX_COST_USD", "NaN"),
        ("ENABLE_CODE_BUILDER", "maybe"),
    ],
)
def test_invalid_configuration_is_rejected(name, value):
    with pytest.raises(ValueError, match=name):
        Settings.from_environment({name: value})


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("APP_PROFILE", "production-like"),
        ("LLM_PROVIDER", "litellm"),
        ("LLM_MODEL", "provider/model"),
        ("LLM_REASONING_EFFORT", "none"),
        ("LLM_RESPONSE_FORMAT", "json_object"),
        ("DATABASE_URL", "postgresql://localhost/ceaa"),
        ("DATABASE_URL", "sqlite:///test.db"),
        ("SANDBOX_BACKEND", "docker"),
        ("ENABLE_CODE_BUILDER", "true"),
        ("BUILDER_MAX_TOKENS", "1000"),
        ("BUILDER_MAX_COST_USD", "1.50"),
    ],
)
def test_unavailable_phase15_adapters_fail_before_creating_database(tmp_path, name, value):
    database = tmp_path / "should-not-exist.db"
    config = Settings.from_environment({name: value})
    with pytest.raises(ValueError):
        Container(
            database_path=None if name == "DATABASE_URL" else str(database),
            runtime_settings=config,
        )
    assert not database.exists()


def test_budget_values_are_exact_decimals():
    config = Settings.from_environment({"BUILDER_MAX_COST_USD": "0.10"})
    assert config.builder_max_cost_usd == Decimal("0.10")


def test_test_profile_requires_explicit_isolated_paths():
    with pytest.raises(ValueError, match="test profile requires"):
        Settings.from_environment({"APP_PROFILE": "test"})


def test_container_reads_environment_at_construction_not_import(tmp_path, monkeypatch):
    first = tmp_path / "first.db"
    second = tmp_path / "second.db"
    monkeypatch.setenv("DATABASE_URL", str(first))
    Container()
    monkeypatch.setenv("DATABASE_URL", str(second))
    Container()
    assert first.exists()
    assert second.exists()
