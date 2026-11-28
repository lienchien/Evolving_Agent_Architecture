import json
from types import SimpleNamespace

import pytest

from src.config import Settings
from src.domain.capability import Capability, Implementation
from src.domain.gap import CapabilityGap
from src.domain.research import UsageSource
from src.infrastructure import ollama_provider
from src.infrastructure.ollama_provider import OllamaProvider
from src.infrastructure.structured_llm import ProviderAdapterError
from src.main import Container
from src.ollama_model_benchmark import TASKS, case_quality
from src.provider_preflight import check_provider_prerequisites


MODEL = "qwen2.5-coder:3b-instruct-q4_K_M"
CAPABILITY = Capability(
    name="word_count", task_family="words",
    implementation=Implementation(code="def run(input): return {}"),
)
GAP = CapabilityGap(task_family="words", description="Count words", task_input={"text": "private sample"})
CASE = {"name": "empty", "input": {"text": ""}, "expected_output": {"word_count": 0}}
GENERATED = dict(
    name="words", description="Count words", code="not executed", dependencies=[],
    inputs=["text"], outputs=["word_count"], functional_test_cases=[CASE],
)


def mock_api(monkeypatch, *, overrides=None, model_info=None):
    calls = []

    def request(self, path, body=None):
        calls.append((path, body))
        if path == "/api/tags":
            return {"models": [model_info if model_info is not None else {
                "name": MODEL, "size": 100, "digest": "sha256",
            }]}
        content = {"test_cases": [CASE]} if body["format"]["title"] == "_BoundaryPayload" else GENERATED
        return {
            "model": MODEL, "done": True, "done_reason": "stop",
            "message": {"content": json.dumps(content)}, "prompt_eval_count": 12, "eval_count": 8,
            **(overrides or {}),
        }

    monkeypatch.setattr(OllamaProvider, "_http", request)
    return calls


def test_native_requests_reuse_schema_and_record_usage(monkeypatch):
    calls = mock_api(monkeypatch)
    adapter = OllamaProvider(model=MODEL, max_output_tokens=500, context_tokens=2048)
    generated = adapter.generate_capability(GAP)
    assert generated.value.functional_test_cases == [CASE]
    assert adapter.generate_boundary_tests(CAPABILITY).value == [CASE]
    payloads = [payload for path, payload in calls if path == "/api/chat"]
    assert len(payloads) == 2
    assert "private sample" not in json.dumps(payloads[0])
    for payload in payloads:
        assert payload["stream"] is False
        assert payload["format"]["additionalProperties"] is False
        assert payload["options"]["num_ctx"] == 2048
        assert payload["options"]["num_predict"] == 500
    usage = generated.usage
    assert (usage.provider, usage.model, usage.source) == ("ollama", MODEL, UsageSource.PROVIDER_REPORTED)
    assert (usage.input_tokens, usage.output_tokens, usage.total_tokens) == (12, 8, 20)
    assert usage.provider_cost_usd is None


@pytest.mark.parametrize("overrides", [
    {"done": False}, {"done_reason": "length"}, {"message": {"content": "not JSON"}},
    {"message": {"content": "{}"}}, {"model": "different:tag"},
])
def test_bad_responses_are_rejected(monkeypatch, overrides):
    mock_api(monkeypatch, overrides=overrides)
    with pytest.raises(ProviderAdapterError):
        OllamaProvider(model=MODEL).generate_boundary_tests(CAPABILITY)


@pytest.mark.parametrize("entry", [
    {"name": MODEL, "size": 100, "digest": "sha256", "remote_model": "some-model"},
    {"name": MODEL, "size": 100, "digest": "sha256", "remote_host": "cloud"},
    {"name": MODEL, "size": 0, "digest": "sha256"},
    {"name": "different:tag", "size": 100, "digest": "sha256"},
])
def test_refuses_to_send_prompt_without_verified_local_tag(monkeypatch, entry):
    calls = mock_api(monkeypatch, model_info=entry)
    with pytest.raises(ProviderAdapterError, match="local"):
        OllamaProvider(model=MODEL).generate_capability(GAP)
    assert calls == [("/api/tags", None)]


@pytest.mark.parametrize("tag", ["model", "model:cloud", "model:7b-cloud", "remote/model:7b", "model:with space"])
def test_rejects_implicit_or_cloud_tags(tag):
    with pytest.raises(ValueError):
        OllamaProvider(model=tag)


def test_limits_settings_preflight_and_api_gate(tmp_path):
    settings = Settings.from_environment({"LLM_PROVIDER": "ollama", "LLM_MODEL": MODEL})
    assert check_provider_prerequisites(settings, {}).configuration_complete
    assert check_provider_prerequisites(settings, {}).credential_variable is None
    adapter = OllamaProvider.from_settings(settings)
    assert adapter.context_tokens == 4096
    db = tmp_path / "blocked.db"
    with pytest.raises(ValueError, match="unavailable"):
        Container(runtime_settings=settings, database_path=str(db))
    with pytest.raises(ValueError, match="sandbox and governance"):
        Container(llm_provider=adapter, database_path=str(db))
    assert not db.exists()
    invalid = Settings.from_environment({
        "LLM_PROVIDER": "ollama", "LLM_MODEL": MODEL, "LLM_RESPONSE_FORMAT": "json_object",
    })
    assert not check_provider_prerequisites(invalid, {}).configuration_complete
    with pytest.raises(ValueError, match="smaller"):
        OllamaProvider(model=MODEL, max_output_tokens=512, context_tokens=512)


def test_loopback_transport_does_not_follow_redirect_or_read_error_body(monkeypatch):
    class RedirectingConnection:
        def __init__(self, host, port, *, timeout):
            assert (host, port, timeout) == ("127.0.0.1", 11434, 60.0)

        def request(self, method, path):
            assert (method, path) == ("GET", "/api/tags")

        def getresponse(self):
            return SimpleNamespace(status=302)

        def close(self):
            pass

    monkeypatch.setattr(ollama_provider, "HTTPConnection", RedirectingConnection)
    with pytest.raises(ProviderAdapterError, match="HTTP 302"):
        OllamaProvider(model=MODEL).model_info()


def test_single_inference_slot_and_release(monkeypatch):
    mock_api(monkeypatch)
    adapter = OllamaProvider(model=MODEL)
    with ollama_provider._INFERENCE_SLOT:
        with pytest.raises(ProviderAdapterError, match="in flight"):
            adapter.generate_boundary_tests(CAPABILITY)
    assert adapter.generate_boundary_tests(CAPABILITY).value == [CASE]


def test_benchmark_oracle_checks_values_and_rejects_bool():
    cases = [
        {"input": {"text": "one\ttwo"}, "expected_output": {"word_count": 2}},
        {"input": {"text": "one"}, "expected_output": {"word_count": True}},
        {"input": {"text": "one two"}, "expected_output": {"word_count": 1}},
    ]
    assert case_quality(TASKS[0], cases) == {"cases": 3, "correct_expected_outputs": 1}
    chars = [{"input": {"text": "貓🙂"}, "expected_output": {"char_count": 2}}]
    assert case_quality(TASKS[1], chars)["correct_expected_outputs"] == 1
