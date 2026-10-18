from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _require_timezone(value: datetime | None) -> datetime | None:
    if value is not None and (value.tzinfo is None or value.utcoffset() is None):
        raise ValueError("telemetry timestamps must include a timezone")
    return value


class TraceOutcome(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    PARTIAL = "partial"
    CANCELLED = "cancelled"


class ObservationKind(str, Enum):
    EXECUTION = "execution"
    RETRY = "retry"
    FALLBACK = "fallback"
    POLICY = "policy"


class ObservationOutcome(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FailureStage(str, Enum):
    ROUTING = "routing"
    CAPABILITY_SELECTION = "capability_selection"
    SKILL_SELECTION = "skill_selection"
    TOOL_EXECUTION = "tool_execution"
    POLICY = "policy"
    PROVIDER = "provider"
    RUNTIME = "runtime"
    VALIDATION = "validation"
    UNKNOWN = "unknown"


class FailureCategory(str, Enum):
    WRONG_SELECTION = "wrong_selection"
    UNAVAILABLE = "unavailable"
    TIMEOUT = "timeout"
    REJECTED = "rejected"
    VALIDATION = "validation"
    EXECUTION = "execution"
    DEPENDENCY = "dependency"
    RESOURCE = "resource"
    UNKNOWN = "unknown"


class RecoveryStrategy(str, Enum):
    RETRY = "retry"
    FALLBACK = "fallback"
    HUMAN_ESCALATION = "human_escalation"


class ExecutionTrace(BaseModel):
    """One task's durable correlation root.

    ``metadata`` must contain sanitized operational metadata only; raw task
    payloads and secrets do not belong in telemetry storage.
    """

    trace_id: str = Field(default_factory=lambda: _new_id("TRACE"))
    task_id: str
    task_family: str
    started_at: datetime = Field(default_factory=_utc_now)
    completed_at: datetime | None = None
    final_outcome: TraceOutcome | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    _timestamps_are_aware = field_validator("started_at", "completed_at")(
        _require_timezone
    )

    @model_validator(mode="after")
    def validate_completion(self) -> ExecutionTrace:
        if (self.completed_at is None) != (self.final_outcome is None):
            raise ValueError("completed_at and final_outcome must be set together")
        if self.completed_at is not None and self.completed_at < self.started_at:
            raise ValueError("completed_at cannot precede started_at")
        return self


class RoutingDecision(BaseModel):
    decision_id: str = Field(default_factory=lambda: _new_id("ROUTE"))
    trace_id: str
    parent_decision_id: str | None = None
    depth: int = Field(default=0, ge=0)
    layer: str
    node_type: str
    candidate_ids: list[str] = Field(default_factory=list)
    selected_target_id: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    score: float | None = None
    decision_model: str | None = None
    decision_model_version: str | None = None
    latency_ms: float | None = Field(default=None, ge=0)
    fallback_reason: str | None = None
    override_reason: str | None = None
    recorded_at: datetime = Field(default_factory=_utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)

    _timestamp_is_aware = field_validator("recorded_at")(_require_timezone)

    @model_validator(mode="after")
    def validate_parent(self) -> RoutingDecision:
        if self.parent_decision_id == self.decision_id:
            raise ValueError("a routing decision cannot be its own parent")
        if self.depth == 0 and self.parent_decision_id is not None:
            raise ValueError("a root routing decision cannot have a parent")
        if self.depth > 0 and self.parent_decision_id is None:
            raise ValueError("a nested routing decision requires a parent")
        return self


class ExecutionObservation(BaseModel):
    observation_id: str = Field(default_factory=lambda: _new_id("OBS"))
    trace_id: str
    decision_id: str | None = None
    parent_observation_id: str | None = None
    kind: ObservationKind = ObservationKind.EXECUTION
    target_type: str
    target_id: str
    outcome: ObservationOutcome
    started_at: datetime = Field(default_factory=_utc_now)
    completed_at: datetime = Field(default_factory=_utc_now)
    latency_ms: float | None = Field(default=None, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    _timestamps_are_aware = field_validator("started_at", "completed_at")(
        _require_timezone
    )

    @model_validator(mode="after")
    def validate_observation(self) -> ExecutionObservation:
        if self.parent_observation_id == self.observation_id:
            raise ValueError("an execution observation cannot be its own parent")
        if self.completed_at < self.started_at:
            raise ValueError("completed_at cannot precede started_at")
        return self


class ExecutionFailure(BaseModel):
    failure_id: str = Field(default_factory=lambda: _new_id("FAIL"))
    trace_id: str
    observation_id: str
    stage: FailureStage
    category: FailureCategory
    error_code: str | None = None
    exception_type: str | None = None
    error_summary: str | None = Field(default=None, max_length=2048)
    recoverable: bool | None = None
    recorded_at: datetime = Field(default_factory=_utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)

    _timestamp_is_aware = field_validator("recorded_at")(_require_timezone)


class RecoveryAttempt(BaseModel):
    recovery_id: str = Field(default_factory=lambda: _new_id("RECOVERY"))
    trace_id: str
    failure_id: str
    observation_id: str
    strategy: RecoveryStrategy
    target_type: str
    target_id: str
    attempt_number: int = Field(ge=1)
    outcome: ObservationOutcome
    recorded_at: datetime = Field(default_factory=_utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)

    _timestamp_is_aware = field_validator("recorded_at")(_require_timezone)
