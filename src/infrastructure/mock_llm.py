from __future__ import annotations

from typing import Any

from src.domain.capability import Capability
from src.domain.gap import CapabilityGap
from src.interfaces.llm import GeneratedCapability, LLMProvider

_CSV_CODE = '''
import csv
import io


def run(input: dict) -> dict:
    csv_text = input["csv_text"]
    reader = csv.reader(io.StringIO(csv_text))
    rows = list(reader)
    header, data_rows = rows[0], rows[1:]
    stats = {}
    for col_index, col_name in enumerate(header):
        values = []
        for row in data_rows:
            try:
                values.append(float(row[col_index]))
            except (ValueError, IndexError):
                pass
        if values:
            stats[col_name] = {
                "count": len(values),
                "sum": sum(values),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
            }
    return {"statistics": stats}
'''.strip()

_WORD_COUNT_CODE = '''
def run(input: dict) -> dict:
    text = input.get("text", "")
    words = text.split()
    return {"word_count": len(words), "char_count": len(text)}
'''.strip()


class MockLLMProvider(LLMProvider):
    """Deterministic template-based stand-in for a real LLM.

    Picks a canned implementation based on keywords in the gap description /
    task family, so the full Generate -> Validate -> Test loop can be proven
    end-to-end before a real LiteLLM-backed provider is wired in.
    """

    def generate_capability(self, gap: CapabilityGap) -> GeneratedCapability:
        haystack = f"{gap.task_family} {gap.description}".lower()

        if "csv" in haystack:
            return GeneratedCapability(
                name="csv_column_summary",
                description="Summarize numeric columns of a CSV file.",
                code=_CSV_CODE,
                dependencies=[],
                inputs=["csv_text"],
                outputs=["statistics"],
                functional_test_cases=[
                    {
                        "name": "basic_two_column_csv",
                        "input": {"csv_text": "a,b\n1,2\n3,4\n"},
                        "expected_output": {
                            "statistics": {
                                "a": {"count": 2, "sum": 4.0, "avg": 2.0, "min": 1.0, "max": 3.0},
                                "b": {"count": 2, "sum": 6.0, "avg": 3.0, "min": 2.0, "max": 4.0},
                            }
                        },
                    }
                ],
            )

        return GeneratedCapability(
            name="text_word_count",
            description="Count words and characters in a text input.",
            code=_WORD_COUNT_CODE,
            dependencies=[],
            inputs=["text"],
            outputs=["word_count", "char_count"],
            functional_test_cases=[
                {
                    "name": "basic_sentence",
                    "input": {"text": "hello world"},
                    "expected_output": {"word_count": 2, "char_count": 11},
                }
            ],
        )

    def generate_boundary_tests(self, capability: Capability) -> list[dict[str, Any]]:
        if capability.name == "csv_column_summary":
            return [
                {
                    "name": "empty_csv",
                    "input": {"csv_text": "a,b\n"},
                    "expected_output": {"statistics": {}},
                }
            ]
        return [
            {
                "name": "empty_text",
                "input": {"text": ""},
                "expected_output": {"word_count": 0, "char_count": 0},
            }
        ]
