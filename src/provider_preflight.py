"""Offline configuration check for the future Phase 1.5-B LiteLLM adapter.

This module never makes a provider request or exposes credential values.
Passing the check does not enable the provider in the application runtime.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from typing import Mapping

from src.config import Settings
from src.infrastructure.ollama_provider import OllamaProvider


_CREDENTIALS = {
    "openrouter": "OPENROUTER_API_KEY",
    "nvidia_nim": "NVIDIA_NIM_API_KEY",
}


@dataclass(frozen=True)
class ProviderPreflightResult:
    model_provider: str | None
    credential_variable: str | None
    configuration_complete: bool
    issues: tuple[str, ...]
    network_call_performed: bool = False
    runtime_provider_enabled: bool = False


def check_provider_prerequisites(
    settings: Settings, environ: Mapping[str, str] | None = None
) -> ProviderPreflightResult:
    source = os.environ if environ is None else environ
    issues: list[str] = []
    credential_variable: str | None = None
    model_provider: str | None = None

    if settings.llm_provider == "ollama":
        try:
            OllamaProvider.from_settings(settings)
        except ValueError as error:
            issues.append(str(error))
        return ProviderPreflightResult("ollama", None, not issues, tuple(issues))

    if settings.llm_provider != "litellm":
        issues.append("LLM_PROVIDER must be litellm or ollama for a real-provider preflight")

    model = settings.llm_model
    if not model:
        issues.append("LLM_MODEL is required")
    elif model != model.strip() or any(character.isspace() for character in model):
        issues.append("LLM_MODEL must not contain whitespace")
    else:
        prefix, separator, model_name = model.partition("/")
        if (
            not separator
            or prefix not in _CREDENTIALS
            or any(not segment for segment in model_name.split("/"))
        ):
            issues.append("LLM_MODEL must start with openrouter/ or nvidia_nim/ and include a model name")
        else:
            model_provider = prefix
            credential_variable = _CREDENTIALS[prefix]
            if prefix != "openrouter" and (
                settings.llm_reasoning_effort is not None
                or settings.llm_response_format is not None
            ):
                issues.append("LLM output controls are currently supported only for openrouter")
            if not source.get(credential_variable, "").strip():
                issues.append(f"{credential_variable} is required")

    return ProviderPreflightResult(
        model_provider=model_provider,
        credential_variable=credential_variable,
        configuration_complete=not issues,
        issues=tuple(issues),
    )


def main() -> int:
    settings = Settings.from_environment()
    result = check_provider_prerequisites(settings)
    print(json.dumps(asdict(result), ensure_ascii=False))
    return 0 if result.configuration_complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
