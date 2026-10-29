from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _require_timezone(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("recovery timestamps must include a timezone")
    return value


class RecoveryGateStatus(str, Enum):
    APPROVED = "approved"
    DENIED = "denied"
    UNKNOWN = "unknown"


class RecoveryResolution(str, Enum):
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    ESCALATED = "escalated"


class FailureAnalysis(BaseModel):
    """Sanitized diagnostic hypothesis and its inspectable evidence."""

    analysis_id: str = Field(default_factory=lambda: _new_id("ANALYSIS"))
    trace_id: str
    failure_id: str
    diagnosis_summary: str = Field(max_length=2048)
    evidence_refs: list[str] = Field(default_factory=list)
    analyzer: str
    analyzer_version: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    recorded_at: datetime = Field(default_factory=_utc_now)

    _timestamp_is_aware = field_validator("recorded_at")(_require_timezone)


class RecoveryPlan(BaseModel):
    """A versioned proposal only; this model grants no execution authority."""

    recovery_plan_id: str = Field(default_factory=lambda: _new_id("RECOVERY-PLAN"))
    trace_id: str
    failure_id: str
    analysis_id: str | None = None
    plan_version: str = "1.0"
    candidate_action: str = Field(max_length=2048)
    scope: list[str] = Field(default_factory=list)
    risk_level: str = "unknown"
    evidence_requirements: list[str] = Field(default_factory=list)
    rollback_plan: str | None = Field(default=None, max_length=2048)
    checkpoint_ref: str | None = None
    max_repair_cycles: int = Field(default=0, ge=0)
    estimated_tokens: int | None = Field(default=None, ge=0)
    estimated_cost_usd: float | None = Field(default=None, ge=0)
    estimated_latency_ms: float | None = Field(default=None, ge=0)
    created_at: datetime = Field(default_factory=_utc_now)

    _timestamp_is_aware = field_validator("created_at")(_require_timezone)


class RecoveryGateResult(BaseModel):
    status: RecoveryGateStatus
    resume_allowed: bool = False
    reason_codes: list[str] = Field(default_factory=list)
    required_approvals: list[str] = Field(default_factory=list)
    policy_version: str | None = None
    reviewed_at: datetime = Field(default_factory=_utc_now)

    _timestamp_is_aware = field_validator("reviewed_at")(_require_timezone)

    @model_validator(mode="after")
    def fail_closed(self) -> RecoveryGateResult:
        if self.status is not RecoveryGateStatus.APPROVED and self.resume_allowed:
            raise ValueError("denied or unknown recovery gates must fail closed")
        return self


class RecoveryOutcome(BaseModel):
    outcome_id: str = Field(default_factory=lambda: _new_id("RECOVERY-OUTCOME"))
    trace_id: str
    failure_id: str
    recovery_plan_id: str | None = None
    gate_status: RecoveryGateStatus
    diagnosis_summary: str | None = Field(default=None, max_length=2048)
    attempted_remediation: str | None = Field(default=None, max_length=2048)
    validation_result: str | None = Field(default=None, max_length=2048)
    resolution: RecoveryResolution
    token_count: int | None = Field(default=None, ge=0)
    cost_usd: float | None = Field(default=None, ge=0)
    latency_ms: float | None = Field(default=None, ge=0)
    recorded_at: datetime = Field(default_factory=_utc_now)

    _timestamp_is_aware = field_validator("recorded_at")(_require_timezone)

    @model_validator(mode="after")
    def validate_resolution(self) -> RecoveryOutcome:
        if (
            self.gate_status is not RecoveryGateStatus.APPROVED
            and self.resolution is RecoveryResolution.RESOLVED
        ):
            raise ValueError("a denied or unknown gate cannot record a resolved recovery")
        if (
            self.resolution is RecoveryResolution.RESOLVED
            and not self.validation_result
        ):
            raise ValueError("a resolved recovery requires independent validation evidence")
        return self
