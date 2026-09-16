from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TestCaseResult(BaseModel):
    name: str
    test_type: str
    passed: bool
    input: dict[str, Any]
    expected_output: dict[str, Any] | None = None
    actual_output: dict[str, Any] | None = None
    error: str | None = None


class TestReport(BaseModel):
    capability_id: str
    capability_version: str
    test_cases: list[TestCaseResult] = Field(default_factory=list)
    pass_rate: float = 0.0
    failed_cases: list[str] = Field(default_factory=list)
    known_limitations: list[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.MEDIUM
    recommended_action: str = "manual_review"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_markdown(self) -> str:
        lines = [
            f"# Test Report — {self.capability_id} v{self.capability_version}",
            "",
            f"- Pass rate: {self.pass_rate:.0%}",
            f"- Risk level: {self.risk_level.value}",
            f"- Recommended action: {self.recommended_action}",
            "",
            "## Test Cases",
        ]
        for tc in self.test_cases:
            status = "PASS" if tc.passed else "FAIL"
            lines.append(f"- [{status}] ({tc.test_type}) {tc.name}")
            if not tc.passed and tc.error:
                lines.append(f"  - error: {tc.error}")
        if self.known_limitations:
            lines.append("")
            lines.append("## Known Limitations")
            for lim in self.known_limitations:
                lines.append(f"- {lim}")
        return "\n".join(lines)
