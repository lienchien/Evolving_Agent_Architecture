"""Shared prompts and validation for isolated real-model adapters."""

from __future__ import annotations

import json
from abc import abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, StrictStr

from src.domain.capability import Capability
from src.domain.gap import CapabilityGap
from src.domain.research import TokenUsage
from src.interfaces.llm import GeneratedCapability, LLMProvider, LLMResponse


class ProviderAdapterError(RuntimeError):
    """Sanitized provider/response failure safe for existing telemetry."""


class _TestCase(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    name: StrictStr = Field(min_length=1, max_length=120)
    input: dict[str, Any]
    expected_output: dict[str, Any]


class _CapabilityPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    name: StrictStr = Field(min_length=1, max_length=120)
    description: StrictStr = Field(min_length=1, max_length=1000)
    code: StrictStr = Field(min_length=1, max_length=50000)
    dependencies: list[StrictStr] = Field(max_length=20)
    inputs: list[StrictStr] = Field(min_length=1, max_length=20)
    outputs: list[StrictStr] = Field(min_length=1, max_length=20)
    functional_test_cases: list[_TestCase] = Field(min_length=1, max_length=20)


class _BoundaryPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    test_cases: list[_TestCase] = Field(min_length=1, max_length=20)


def parse_payload(content: Any, schema: type[BaseModel]) -> BaseModel:
    if not isinstance(content, str) or not content or len(content) > 100_000:
        raise ProviderAdapterError("LLM response content is missing or oversized")
    try:
        return schema.model_validate(json.loads(content))
    except (ValueError, RecursionError):
        raise ProviderAdapterError("LLM response is not valid structured JSON") from None


def token_count(value: Any) -> int | None:
    return value if type(value) is int and value >= 0 else None


class StructuredLLMProvider(LLMProvider):
    """One shared contract; no completion output is executed here."""

    @abstractmethod
    def _request(
        self, messages: list[dict[str, str]], schema: type[BaseModel]
    ) -> tuple[BaseModel, TokenUsage]: ...

    def generate_capability(self, gap: CapabilityGap) -> LLMResponse[GeneratedCapability]:
        messages = [
            {"role": "system", "content": (
                "Return one JSON object only, without markdown or prose. Keys: name, "
                "description, code, dependencies, inputs, outputs, functional_test_cases. "
                "Each test case needs name, input and expected_output. The Python code "
                "must define run(input: dict) -> dict. Do not include credentials."
            )},
            {"role": "user", "content": json.dumps({
                "task_family": gap.task_family,
                "description": gap.description,
                "input_field_names": sorted(str(key) for key in gap.task_input),
            }, ensure_ascii=False)},
        ]
        payload, usage = self._request(messages, _CapabilityPayload)
        assert isinstance(payload, _CapabilityPayload)
        return LLMResponse(
            value=GeneratedCapability(
                name=payload.name, description=payload.description, code=payload.code,
                dependencies=list(payload.dependencies), inputs=list(payload.inputs),
                outputs=list(payload.outputs),
                functional_test_cases=[case.model_dump() for case in payload.functional_test_cases],
            ),
            usage=usage,
        )

    def generate_boundary_tests(
        self, capability: Capability
    ) -> LLMResponse[list[dict[str, Any]]]:
        messages = [
            {"role": "system", "content": (
                "Return one JSON object only with a test_cases array. Each case "
                "must contain name, input and expected_output. Create boundary "
                "tests for this Python run(input: dict) -> dict implementation."
            )},
            {"role": "user", "content": json.dumps({
                "name": capability.name,
                "description": capability.description,
                "inputs": capability.inputs,
                "outputs": capability.outputs,
                "code": capability.implementation.code,
            }, ensure_ascii=False)},
        ]
        payload, usage = self._request(messages, _BoundaryPayload)
        assert isinstance(payload, _BoundaryPayload)
        return LLMResponse(value=[case.model_dump() for case in payload.test_cases], usage=usage)
