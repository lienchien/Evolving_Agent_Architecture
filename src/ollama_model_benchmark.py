"""Compare installed local model sizes on identical, generation-only tasks."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from time import perf_counter
from typing import Any

from src.domain.capability import Capability, Implementation
from src.domain.gap import CapabilityGap
from src.infrastructure.ollama_provider import OllamaProvider
from src.infrastructure.structured_llm import ProviderAdapterError


BASELINE_MODELS = (
    "qwen2.5-coder:3b-instruct-q4_K_M",
    "qwen2.5-coder:7b-instruct-q4_K_M",
)


@dataclass(frozen=True)
class Task:
    field: str
    description: str
    expression: str

    def reference(self, text: str) -> int:
        # Trusted comparator; never evaluate self.expression or model output.
        return len(text.split()) if self.field == "word_count" else len(text)


TASKS = (
    Task("word_count", "Count whitespace-separated words in text.", 'len(input["text"].split())'),
    Task("char_count", "Count Python Unicode code points in text.", 'len(input["text"])'),
)


def case_quality(task: Task, cases: list[dict[str, Any]]) -> dict[str, int]:
    correct = 0
    for case in cases:
        inputs, outputs = case["input"], case["expected_output"]
        text, result = inputs.get("text"), outputs.get(task.field)
        if (
            set(inputs) == {"text"} and isinstance(text, str)
            and set(outputs) == {task.field} and type(result) is int
            and result == task.reference(text)
        ):
            correct += 1
    return {"cases": len(cases), "correct_expected_outputs": correct}


def run_model(adapter: OllamaProvider, repeats: int) -> dict[str, Any]:
    installed = adapter.model_info()
    details = installed.get("details") or {}
    metrics = []
    for repeat in range(1, repeats + 1):
        for task in TASKS:
            capability = Capability(
                name=task.field, description=(
                    f"{task.description} Propose exactly two short tests: empty text and one non-empty example."
                ), task_family=task.field,
                inputs=["text"], outputs=[task.field],
                implementation=Implementation(code=(
                    "def run(input: dict) -> dict:\n"
                    f'    return {{"{task.field}": {task.expression}}}'
                )),
            )
            gap = CapabilityGap(
                task_family=task.field,
                description=(
                    f"{task.description} Use only a string text input and return only integer "
                    f"{task.field}. No dependencies. Include exactly one short functional test."
                ),
                task_input={"text": ""},
            )
            for operation in ("capability", "boundary"):
                row = {
                    "task": task.field, "operation": operation, "repeat": repeat,
                    "resident_before": adapter.loaded_info() is not None,
                }
                start = perf_counter()
                try:
                    if operation == "capability":
                        result = adapter.generate_capability(gap)
                        quality = case_quality(task, result.value.functional_test_cases)
                        contract = (
                            result.value.inputs == ["text"] and result.value.outputs == [task.field]
                            and result.value.dependencies == [] and quality["cases"] == 1
                        )
                    else:
                        result = adapter.generate_boundary_tests(capability)
                        quality = case_quality(task, result.value)
                        texts = [case["input"].get("text") for case in result.value]
                        contract = len(texts) == 2 and texts.count("") == 1
                    row.update(
                        schema_pass=True, contract_pass=contract, **quality,
                        usage=result.usage.model_dump(mode="json", exclude_none=True),
                    )
                except ProviderAdapterError as error:
                    row.update(schema_pass=False, contract_pass=False, error=str(error))
                row["wall_seconds"] = round(perf_counter() - start, 3)
                loaded = adapter.loaded_info()
                if loaded is not None:
                    row.update(
                        loaded_bytes=loaded.get("size"), gpu_bytes=loaded.get("size_vram"),
                        actual_context_tokens=loaded.get("context_length"),
                    )
                metrics.append(row)
    return {
        "model": adapter.model, "digest": installed["digest"], "model_bytes": installed["size"],
        "parameter_size": details.get("parameter_size"), "quantization": details.get("quantization_level"),
        "ollama_version": adapter.server_version(), "context_tokens": adapter.context_tokens,
        "output_token_cap": adapter.max_output_tokens, "timeout_seconds": adapter.timeout,
        "runs": metrics,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", default=BASELINE_MODELS)
    parser.add_argument("--repeats", type=int, choices=range(1, 6), default=1)
    args = parser.parse_args()
    if len(set(args.models)) < 2 or len(set(args.models)) != len(args.models):
        parser.error("provide at least two distinct installed local model tags")
    try:
        adapters = [
            OllamaProvider(model=model, request_timeout_seconds=90, max_output_tokens=512)
            for model in args.models
        ]
        for adapter in adapters:
            adapter.model_info()
        for adapter in adapters:
            print(json.dumps(run_model(adapter, args.repeats), ensure_ascii=False), flush=True)
    except (ValueError, ProviderAdapterError) as error:
        parser.exit(2, f"Benchmark unavailable: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
