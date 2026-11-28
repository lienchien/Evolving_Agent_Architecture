from __future__ import annotations

import math
import os
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Mapping


def _integer(source: Mapping[str, str], name: str, default: int, maximum: int) -> int:
    raw = source.get(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if not 0 <= value <= maximum:
        raise ValueError(f"{name} must be between 0 and {maximum}")
    return value


def _positive_float(source: Mapping[str, str], name: str, default: float) -> float:
    raw = source.get(name, str(default)).strip()
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a positive number") from exc
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a positive finite number")
    return value


def _nonnegative_decimal(source: Mapping[str, str], name: str) -> Decimal:
    try:
        value = Decimal(source.get(name, "0").strip())
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be a nonnegative number") from exc
    if not value.is_finite() or value < 0:
        raise ValueError(f"{name} must be a nonnegative finite number")
    return value


def _boolean(source: Mapping[str, str], name: str, default: bool = False) -> bool:
    raw = source.get(name, str(default)).strip().lower()
    if raw in {"true", "1", "yes", "on"}:
        return True
    if raw in {"false", "0", "no", "off"}:
        return False
    raise ValueError(f"{name} must be true or false")


@dataclass(frozen=True)
class Settings:
    profile: str = "development"
    llm_provider: str = "mock"
    llm_model: str | None = None
    llm_request_timeout_seconds: float = 30.0
    llm_max_output_tokens: int = 2048
    llm_reasoning_effort: str | None = None
    llm_response_format: str | None = None
    ollama_context_tokens: int = 4096
    database_path: str = "capability_library.db"
    report_directory: str = "capability_library"
    sandbox_backend: str = "subprocess"
    sandbox_timeout_seconds: float = 5.0
    retry_hard_max: int = 3
    retry_backoff_ms: int = 0
    builder_max_tokens: int = 0
    builder_max_cost_usd: Decimal = Decimal("0")
    enable_code_builder: bool = False

    @classmethod
    def from_environment(cls, environ: Mapping[str, str] | None = None) -> Settings:
        source = os.environ if environ is None else environ
        profile = source.get("APP_PROFILE", "development").strip().lower()
        if profile not in {"development", "test", "production-like"}:
            raise ValueError("APP_PROFILE must be development, test, or production-like")
        if profile == "test" and not {"DATABASE_URL", "REPORT_DIRECTORY"}.issubset(source):
            raise ValueError("test profile requires DATABASE_URL and REPORT_DIRECTORY")
        provider = source.get("LLM_PROVIDER", "mock").strip().lower()
        if provider not in {"mock", "litellm", "ollama"}:
            raise ValueError("LLM_PROVIDER must be mock, litellm, or ollama")
        sandbox = source.get("SANDBOX_BACKEND", "subprocess").strip().lower()
        if sandbox not in {"subprocess", "docker"}:
            raise ValueError("SANDBOX_BACKEND must be subprocess or docker")
        database_path = source.get("DATABASE_URL", "capability_library.db").strip()
        if not database_path:
            raise ValueError("DATABASE_URL must not be empty")
        report_directory = source.get("REPORT_DIRECTORY", "capability_library").strip()
        if not report_directory:
            raise ValueError("REPORT_DIRECTORY must not be empty")
        model = source.get("LLM_MODEL", "").strip() or None
        max_output_tokens = _integer(source, "LLM_MAX_OUTPUT_TOKENS", 2048, 8192)
        if max_output_tokens == 0:
            raise ValueError("LLM_MAX_OUTPUT_TOKENS must be between 1 and 8192")
        reasoning_effort = source.get("LLM_REASONING_EFFORT", "").strip().lower() or None
        if reasoning_effort not in {None, "none", "minimal", "low", "medium", "high", "xhigh", "max"}:
            raise ValueError("LLM_REASONING_EFFORT is unsupported")
        response_format = source.get("LLM_RESPONSE_FORMAT", "").strip().lower() or None
        if response_format not in {None, "json_object"}:
            raise ValueError("LLM_RESPONSE_FORMAT must be json_object or empty")
        ollama_context_tokens = _integer(source, "OLLAMA_CONTEXT_TOKENS", 4096, 32768)
        if ollama_context_tokens < 512:
            raise ValueError("OLLAMA_CONTEXT_TOKENS must be between 512 and 32768")
        return cls(
            profile=profile,
            llm_provider=provider,
            llm_model=model,
            llm_request_timeout_seconds=_positive_float(
                source, "LLM_REQUEST_TIMEOUT_SECONDS", 30.0
            ),
            llm_max_output_tokens=max_output_tokens,
            llm_reasoning_effort=reasoning_effort,
            llm_response_format=response_format,
            ollama_context_tokens=ollama_context_tokens,
            database_path=database_path,
            report_directory=report_directory,
            sandbox_backend=sandbox,
            sandbox_timeout_seconds=_positive_float(
                source, "SANDBOX_TIMEOUT_SECONDS", 5.0
            ),
            retry_hard_max=_integer(source, "RETRY_HARD_MAX", 3, 3),
            retry_backoff_ms=_integer(source, "RETRY_BACKOFF_MS", 0, 60000),
            builder_max_tokens=_integer(source, "BUILDER_MAX_TOKENS", 0, 10000000),
            builder_max_cost_usd=_nonnegative_decimal(source, "BUILDER_MAX_COST_USD"),
            enable_code_builder=_boolean(source, "ENABLE_CODE_BUILDER"),
        )

    def validate_available_adapters(self, *, database_path: str | None = None) -> None:
        """Fail closed rather than silently running mock adapters in another profile."""
        if self.profile == "production-like":
            raise ValueError("production-like profile is unavailable until Phase 1.5 security gates")
        if self.llm_provider != "mock":
            raise ValueError("real LLM providers are unavailable until Phase 1.5-B")
        if self.llm_model is not None:
            raise ValueError("LLM_MODEL is unavailable with the mock provider")
        if self.llm_reasoning_effort is not None or self.llm_response_format is not None:
            raise ValueError("LLM output controls are unavailable with the mock provider")
        for candidate in (self.database_path, database_path):
            if candidate is None:
                continue
            if candidate.lower().startswith(("postgres://", "postgresql://")):
                raise ValueError("PostgreSQL is unavailable until Phase 1.5-C")
            if "://" in candidate:
                raise ValueError("DATABASE_URL currently requires a SQLite file path, not a DSN")
        if self.sandbox_backend != "subprocess":
            raise ValueError("Docker sandbox is unavailable until Phase 1.5-D")
        if self.enable_code_builder:
            raise ValueError("Code Builder is unavailable until Phase 1.5-E")
        if self.builder_max_tokens or self.builder_max_cost_usd:
            raise ValueError("Builder budgets are unavailable until Phase 1.5-E")
