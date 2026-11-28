from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from src.config import Settings
from src.domain.capability import Capability, Implementation
from src.domain.gap import CapabilityGap
from src.domain.research import UsageSource
from src.infrastructure.litellm_provider import LiteLLMProvider, ProviderAdapterError
from src.main import Container


_GENERATED = {
    "name": "word_count",
    "description": "Count words",
    "code": "def run(input: dict) -> dict:\n    return {'word_count': len(input['text'].split())}",
    "dependencies": [],
    "inputs": ["text"],
    "outputs": ["word_count"],
    "functional_test_cases": [
        {"name": "basic", "input": {"text": "one two"}, "expected_output": {"word_count": 2}}
    ],
}


def _response(content, *, usage=None, finish_reason="stop"):
    return {
        "choices": [{"finish_reason": finish_reason, "message": {"content": content}}],
        "model": "vendor/actual-model",
        "usage": usage,
    }


def test_adapter_parses_capability_and_reported_usage_without_input_values():
    calls = []

    def fake_completion(**kwargs):
        calls.append(kwargs)
        return _response(
            json.dumps(_GENERATED),
            usage={
                "prompt_tokens": 15,
                "completion_tokens": 25,
                "total_tokens": 40,
                "completion_tokens_details": {"reasoning_tokens": 3},
                "cost": 0.001,
            },
        )

    adapter = LiteLLMProvider(
        model="openrouter/vendor/model",
        request_timeout_seconds=12,
        max_output_tokens=512,
        completion_fn=fake_completion,
    )
    result = adapter.generate_capability(
        CapabilityGap(task_family="words", description="Count words", task_input={"text": "private-input"})
    )

    assert result.value.name == "word_count"
    assert result.value.functional_test_cases[0]["expected_output"] == {"word_count": 2}
    assert result.usage.provider == "openrouter"
    assert result.usage.model == "vendor/actual-model"
    assert result.usage.source is UsageSource.PROVIDER_REPORTED
    assert (result.usage.input_tokens, result.usage.output_tokens) == (15, 25)
    assert result.usage.reasoning_tokens == 3
    assert result.usage.provider_cost_usd == 0.001
    assert len(calls) == 1
    assert calls[0]["request_timeout"] == 12
    assert calls[0]["max_tokens"] == 512
    assert calls[0]["num_retries"] == calls[0]["max_retries"] == 0
    assert "reasoning_effort" not in calls[0]
    assert "response_format" not in calls[0]
    assert "private-input" not in json.dumps(calls[0])
    assert "text" in json.dumps(calls[0])


def test_adapter_parses_boundary_tests_and_preserves_missing_usage():
    response = _response(json.dumps({
        "test_cases": [
            {"name": "empty", "input": {"text": ""}, "expected_output": {"word_count": 0}}
        ]
    }))
    adapter = LiteLLMProvider(
        model="nvidia_nim/vendor/model", completion_fn=lambda **_: response
    )
    capability = Capability(
        name="word_count", task_family="words", inputs=["text"], outputs=["word_count"],
        implementation=Implementation(code=_GENERATED["code"]),
    )
    result = adapter.generate_boundary_tests(capability)
    assert result.value[0]["name"] == "empty"
    assert result.usage.source is UsageSource.UNAVAILABLE
    assert result.usage.total_tokens is None
    assert result.usage.provider_cost_usd is None


def test_openrouter_output_controls_are_forwarded_to_both_generation_methods():
    calls = []
    responses = iter([
        _response(json.dumps(_GENERATED)),
        _response(json.dumps({
            "test_cases": [
                {"name": "empty", "input": {"text": ""}, "expected_output": {"word_count": 0}}
            ]
        })),
    ])

    def fake_completion(**kwargs):
        calls.append(kwargs)
        return next(responses)

    adapter = LiteLLMProvider(
        model="openrouter/inclusionai/ling-3.2-flash:free",
        reasoning_effort="none",
        response_format="json_object",
        completion_fn=fake_completion,
    )
    generated = adapter.generate_capability(CapabilityGap(task_family="words", description="Count"))
    capability = Capability(
        name=generated.value.name, task_family="words",
        inputs=generated.value.inputs, outputs=generated.value.outputs,
        implementation=Implementation(code=generated.value.code),
    )
    boundary = adapter.generate_boundary_tests(capability)

    assert len(boundary.value) == 1
    assert len(calls) == 2
    assert all(call["reasoning_effort"] == "none" for call in calls)
    assert all(call["response_format"] == {"type": "json_object"} for call in calls)
    assert all(call["num_retries"] == call["max_retries"] == 0 for call in calls)


def test_adapter_accepts_object_style_litellm_response():
    response = SimpleNamespace(
        choices=[SimpleNamespace(
            finish_reason="stop",
            message=SimpleNamespace(content=json.dumps(_GENERATED)),
        )],
        model="vendor/actual-model",
        usage=SimpleNamespace(prompt_tokens=8, completion_tokens=None, total_tokens=None),
    )
    adapter = LiteLLMProvider(
        model="openrouter/vendor/model", completion_fn=lambda **_: response
    )
    result = adapter.generate_capability(CapabilityGap(task_family="words", description="Count"))
    assert result.usage.input_tokens == 8
    assert result.usage.output_tokens is None


@pytest.mark.parametrize(
    "response",
    [
        {},
        _response("", usage={}),
        _response("```json\n{}\n```"),
        _response(json.dumps(_GENERATED), finish_reason="length"),
        _response(json.dumps({**_GENERATED, "secret": "value"})),
        _response(json.dumps({**_GENERATED, "functional_test_cases": []})),
    ],
)
def test_adapter_rejects_incomplete_or_invalid_output_without_echoing_it(response):
    adapter = LiteLLMProvider(
        model="openrouter/vendor/model", completion_fn=lambda **_: response
    )
    with pytest.raises(ProviderAdapterError) as error:
        adapter.generate_capability(CapabilityGap(task_family="words", description="Count"))
    assert "secret" not in str(error.value)
    assert "value" not in str(error.value)


def test_adapter_sanitizes_provider_exception():
    def fail(**_):
        raise RuntimeError("private-key-and-request-body")

    adapter = LiteLLMProvider(model="openrouter/vendor/model", completion_fn=fail)
    with pytest.raises(ProviderAdapterError, match="LLM request failed") as error:
        adapter.generate_capability(CapabilityGap(task_family="words", description="Count"))
    assert "private-key" not in str(error.value)


def test_adapter_does_not_infer_unreported_tokens_or_cost():
    adapter = LiteLLMProvider(
        model="openrouter/vendor/model",
        completion_fn=lambda **_: _response(
            json.dumps(_GENERATED), usage={"prompt_tokens": -3, "cost": float("nan")}
        ),
    )
    usage = adapter.generate_capability(
        CapabilityGap(task_family="words", description="Count")
    ).usage
    assert usage.source is UsageSource.UNAVAILABLE
    assert usage.input_tokens is None
    assert usage.provider_cost_usd is None


@pytest.mark.parametrize("model", ["openrouter/", "openrouter//model", "nvidia_nim/a b", "other/model"])
def test_adapter_rejects_invalid_model_routes(model):
    with pytest.raises(ValueError, match="model must use"):
        LiteLLMProvider(model=model, completion_fn=lambda **_: None)


@pytest.mark.parametrize(
    ("model", "controls"),
    [
        ("openrouter/vendor/model", {"reasoning_effort": "off"}),
        ("openrouter/vendor/model", {"response_format": "json_schema"}),
        ("nvidia_nim/vendor/model", {"reasoning_effort": "none"}),
        ("nvidia_nim/vendor/model", {"response_format": "json_object"}),
    ],
)
def test_adapter_rejects_invalid_or_unverified_output_controls(model, controls):
    with pytest.raises(ValueError):
        LiteLLMProvider(model=model, completion_fn=lambda **_: None, **controls)


def test_adapter_can_be_built_from_settings_but_not_enter_current_api(tmp_path):
    config = Settings.from_environment({
        "LLM_PROVIDER": "litellm",
        "LLM_MODEL": "openrouter/vendor/model",
        "LLM_REQUEST_TIMEOUT_SECONDS": "8",
        "LLM_MAX_OUTPUT_TOKENS": "256",
        "LLM_REASONING_EFFORT": "none",
        "LLM_RESPONSE_FORMAT": "json_object",
    })
    adapter = LiteLLMProvider.from_settings(
        config, completion_fn=lambda **_: _response(json.dumps(_GENERATED))
    )
    assert adapter._request_timeout_seconds == 8
    assert adapter._max_output_tokens == 256
    assert adapter._reasoning_effort == "none"
    assert adapter._response_format == "json_object"
    database = tmp_path / "blocked.db"
    with pytest.raises(ValueError, match="sandbox and governance"):
        Container(database_path=str(database), llm_provider=adapter)
    assert not database.exists()
