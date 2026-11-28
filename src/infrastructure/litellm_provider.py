"""LiteLLM adapter. Deliberately not wired into the current API container.

Generated code must not reach the Phase 1 subprocess executor. This adapter is
tested with an injected completion function until sandbox and governance gates
are available.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from typing import Any

from pydantic import BaseModel

from src.config import Settings
from src.domain.research import TokenUsage, UsageSource
from src.infrastructure.structured_llm import (
    ProviderAdapterError,
    StructuredLLMProvider,
    parse_payload,
    token_count as _count,
)


def _field(value: Any, name: str) -> Any:
    if isinstance(value, Mapping):
        return value.get(name)
    return getattr(value, name, None)


def _cost(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    amount = float(value)
    return amount if math.isfinite(amount) and amount >= 0 else None


class LiteLLMProvider(StructuredLLMProvider):
    def __init__(
        self,
        *,
        model: str,
        request_timeout_seconds: float = 30.0,
        max_output_tokens: int = 2048,
        reasoning_effort: str | None = None,
        response_format: str | None = None,
        completion_fn: Callable[..., Any] | None = None,
    ) -> None:
        prefix, separator, model_name = model.partition("/")
        if (
            prefix not in {"openrouter", "nvidia_nim"}
            or not separator
            or any(not segment for segment in model_name.split("/"))
            or any(character.isspace() for character in model)
        ):
            raise ValueError("model must use an openrouter/ or nvidia_nim/ prefix")
        if not math.isfinite(request_timeout_seconds) or request_timeout_seconds <= 0:
            raise ValueError("request_timeout_seconds must be positive")
        if (
            not isinstance(max_output_tokens, int)
            or isinstance(max_output_tokens, bool)
            or not 1 <= max_output_tokens <= 8192
        ):
            raise ValueError("max_output_tokens must be between 1 and 8192")
        if reasoning_effort not in {None, "none", "minimal", "low", "medium", "high", "xhigh", "max"}:
            raise ValueError("reasoning_effort is unsupported")
        if response_format not in {None, "json_object"}:
            raise ValueError("response_format must be json_object or None")
        if prefix != "openrouter" and (reasoning_effort is not None or response_format is not None):
            raise ValueError("LLM output controls are currently supported only for openrouter")
        self._model = model
        self._request_timeout_seconds = request_timeout_seconds
        self._max_output_tokens = max_output_tokens
        self._reasoning_effort = reasoning_effort
        self._response_format = response_format
        self._completion_fn = completion_fn

    @classmethod
    def from_settings(
        cls, settings: Settings, *, completion_fn: Callable[..., Any] | None = None
    ) -> LiteLLMProvider:
        if settings.llm_provider != "litellm" or not settings.llm_model:
            raise ValueError("LLM_PROVIDER=litellm and LLM_MODEL are required")
        return cls(
            model=settings.llm_model,
            request_timeout_seconds=settings.llm_request_timeout_seconds,
            max_output_tokens=settings.llm_max_output_tokens,
            reasoning_effort=settings.llm_reasoning_effort,
            response_format=settings.llm_response_format,
            completion_fn=completion_fn,
        )

    def _completion(self, messages: list[dict[str, str]]) -> Any:
        completion = self._completion_fn
        if completion is None:
            try:
                from litellm import completion
            except ImportError:
                raise ProviderAdapterError("LiteLLM SDK is not installed") from None
        try:
            arguments: dict[str, Any] = {
                "model": self._model,
                "messages": messages,
                "request_timeout": self._request_timeout_seconds,
                "max_tokens": self._max_output_tokens,
                "num_retries": 0,
                "max_retries": 0,
            }
            if self._reasoning_effort is not None:
                arguments["reasoning_effort"] = self._reasoning_effort
            if self._response_format == "json_object":
                arguments["response_format"] = {"type": "json_object"}
            return completion(**arguments)
        except Exception:
            # Provider exceptions can include credentials, URLs or request data.
            raise ProviderAdapterError("LLM request failed") from None

    def _request(
        self, messages: list[dict[str, str]], schema: type[BaseModel]
    ) -> tuple[BaseModel, TokenUsage]:
        response = self._completion(messages)
        choices = _field(response, "choices")
        if not isinstance(choices, (list, tuple)) or not choices:
            raise ProviderAdapterError("LLM response has no choices")
        choice = choices[0]
        if _field(choice, "finish_reason") != "stop":
            raise ProviderAdapterError("LLM response did not finish normally")
        content = _field(_field(choice, "message"), "content")
        payload = parse_payload(content, schema)

        raw_usage = _field(response, "usage")
        input_tokens = _count(_field(raw_usage, "prompt_tokens"))
        output_tokens = _count(_field(raw_usage, "completion_tokens"))
        total_tokens = _count(_field(raw_usage, "total_tokens"))
        details = _field(raw_usage, "completion_tokens_details")
        reasoning_tokens = _count(_field(details, "reasoning_tokens"))
        reported_model = _field(response, "model")
        if not isinstance(reported_model, str) or not reported_model or len(reported_model) > 255:
            reported_model = self._model
        usage = TokenUsage(
            provider=self._model.split("/", 1)[0],
            model=reported_model,
            source=(
                UsageSource.PROVIDER_REPORTED
                if any(value is not None for value in (
                    input_tokens, output_tokens, total_tokens, reasoning_tokens
                ))
                else UsageSource.UNAVAILABLE
            ),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            reasoning_tokens=reasoning_tokens,
            total_tokens=total_tokens,
            # Only an explicit provider usage cost is recorded. LiteLLM's
            # completion_cost() is an estimate and is intentionally not used.
            provider_cost_usd=_cost(_field(raw_usage, "cost")),
        )
        return payload, usage
