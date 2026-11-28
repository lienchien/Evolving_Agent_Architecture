"""Local-only Ollama adapter used outside the API runtime."""

from __future__ import annotations

import json
import math
import re
from http.client import HTTPConnection, HTTPException
from threading import Lock
from typing import Any

from pydantic import BaseModel

from src.config import Settings
from src.domain.research import TokenUsage, UsageSource
from src.infrastructure.structured_llm import (
    ProviderAdapterError,
    StructuredLLMProvider,
    parse_payload,
    token_count,
)


_MAX_RESPONSE_BYTES = 1_048_576
_INFERENCE_SLOT = Lock()
_MODEL_TAG = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}:[A-Za-z0-9][A-Za-z0-9_.-]{0,99}")


def is_local_ollama_tag(model: str) -> bool:
    return bool(
        _MODEL_TAG.fullmatch(model)
        and not any("cloud" in re.split(r"[-_.]", part.lower()) for part in model.split(":"))
    )


class OllamaProvider(StructuredLLMProvider):
    def __init__(
        self,
        *,
        model: str,
        request_timeout_seconds: float = 60.0,
        max_output_tokens: int = 1024,
        context_tokens: int = 4096,
    ) -> None:
        if not is_local_ollama_tag(model):
            raise ValueError("LLM_MODEL must be an explicit local Ollama name:tag (no cloud tags)")
        if not math.isfinite(request_timeout_seconds) or request_timeout_seconds <= 0:
            raise ValueError("LLM_REQUEST_TIMEOUT_SECONDS must be positive")
        if type(max_output_tokens) is not int or not 1 <= max_output_tokens <= 8192:
            raise ValueError("LLM_MAX_OUTPUT_TOKENS must be between 1 and 8192")
        if type(context_tokens) is not int or not 512 <= context_tokens <= 32768:
            raise ValueError("OLLAMA_CONTEXT_TOKENS must be between 512 and 32768")
        if max_output_tokens >= context_tokens:
            raise ValueError("LLM_MAX_OUTPUT_TOKENS must be smaller than OLLAMA_CONTEXT_TOKENS")
        self.model = model
        self.timeout = request_timeout_seconds
        self.max_output_tokens = max_output_tokens
        self.context_tokens = context_tokens

    @classmethod
    def from_settings(cls, settings: Settings) -> OllamaProvider:
        if settings.llm_provider != "ollama" or not settings.llm_model:
            raise ValueError("LLM_PROVIDER=ollama and LLM_MODEL are required")
        if settings.llm_reasoning_effort is not None or settings.llm_response_format is not None:
            raise ValueError("OpenRouter output controls must be unset for Ollama")
        return cls(
            model=settings.llm_model,
            request_timeout_seconds=settings.llm_request_timeout_seconds,
            max_output_tokens=settings.llm_max_output_tokens,
            context_tokens=settings.ollama_context_tokens,
        )

    def _http(self, path: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        # Direct loopback connection: no proxy, redirects, keys, retries, pulls or cloud fallback.
        connection = HTTPConnection("127.0.0.1", 11434, timeout=self.timeout)
        try:
            if data is None:
                connection.request("GET", path)
            else:
                connection.request(
                    "POST", path, json.dumps(data, ensure_ascii=False).encode(),
                    {"Content-Type": "application/json"},
                )
            response = connection.getresponse()
            if response.status != 200:
                raise ProviderAdapterError(f"Ollama request rejected (HTTP {response.status})")
            body = response.read(_MAX_RESPONSE_BYTES + 1)
            if len(body) > _MAX_RESPONSE_BYTES:
                raise ProviderAdapterError("Ollama response is oversized")
            result = json.loads(body)
        except TimeoutError:
            raise ProviderAdapterError("Ollama request timed out") from None
        except (OSError, HTTPException, ValueError, RecursionError):
            raise ProviderAdapterError("Ollama response or connection failed") from None
        finally:
            connection.close()
        if not isinstance(result, dict):
            raise ProviderAdapterError("Ollama returned an unexpected response")
        return result

    def model_info(self) -> dict[str, Any]:
        """Readiness check: selected, fully installed, non-remote model."""
        models = self._http("/api/tags").get("models")
        if isinstance(models, list):
            for entry in models:
                if not isinstance(entry, dict) or entry.get("name") != self.model:
                    continue
                if (
                    entry.get("remote_model") or entry.get("remote_host")
                    or not token_count(entry.get("size"))
                    or not entry.get("digest")
                ):
                    raise ProviderAdapterError("Ollama model is not a verified local installation")
                return entry
        raise ProviderAdapterError("Ollama model is not installed locally")

    def server_version(self) -> str | None:
        version = self._http("/api/version").get("version")
        return version if isinstance(version, str) else None

    def loaded_info(self) -> dict[str, Any] | None:
        models = self._http("/api/ps").get("models")
        if isinstance(models, list):
            return next(
                (m for m in models if isinstance(m, dict) and m.get("name") == self.model),
                None,
            )
        return None

    def _request(
        self, messages: list[dict[str, str]], schema: type[BaseModel]
    ) -> tuple[BaseModel, TokenUsage]:
        if not _INFERENCE_SLOT.acquire(blocking=False):
            raise ProviderAdapterError("Ollama adapter already has a request in flight")
        try:
            self.model_info()
            response = self._http("/api/chat", {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "format": schema.model_json_schema(),
                "keep_alive": "2m",
                "options": {
                    "num_ctx": self.context_tokens,
                    "num_predict": self.max_output_tokens,
                    "temperature": 0,
                    "seed": 42,
                },
            })
            if response.get("model") != self.model:
                raise ProviderAdapterError("Ollama returned a different model")
            if response.get("done") is not True or response.get("done_reason") != "stop":
                raise ProviderAdapterError("LLM response did not finish normally")
            message = response.get("message")
            payload = parse_payload(message.get("content") if isinstance(message, dict) else None, schema)
            input_tokens = token_count(response.get("prompt_eval_count"))
            output_tokens = token_count(response.get("eval_count"))
            return payload, TokenUsage(
                provider="ollama",
                model=self.model,
                source=UsageSource.PROVIDER_REPORTED if (
                    input_tokens is not None or output_tokens is not None
                ) else UsageSource.UNAVAILABLE,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=(input_tokens + output_tokens) if (
                    input_tokens is not None and output_tokens is not None
                ) else None,
            )
        finally:
            _INFERENCE_SLOT.release()
