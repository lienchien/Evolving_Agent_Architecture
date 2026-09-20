from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class UsageSource(str, Enum):
    PROVIDER_REPORTED = "provider_reported"
    UNAVAILABLE = "unavailable"
    NOT_APPLICABLE = "not_applicable"


class ResearchPhase(str, Enum):
    GAP_DETECTION = "gap_detection"
    GENERATION = "generation"
    VALIDATION = "validation"
    TESTING = "testing"
    REVISION = "revision"
    REPORT = "report"
    RETRIEVAL = "retrieval"
    ROUTING = "routing"
    REUSE_REASONING = "reuse_reasoning"
    RESPONSE = "response"


class TokenUsage(BaseModel):
    """Usage reported by a provider; missing values stay unknown.

    Token counts must never be estimated when the provider does not report
    them. A provider may still report a reliable monetary cost independently.
    """

    provider: str = "unknown"
    model: str = "unknown"
    source: UsageSource = UsageSource.UNAVAILABLE
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    reasoning_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
    provider_cost_usd: float | None = Field(default=None, ge=0)


class LLMInteractionMetric(BaseModel):
    interaction_id: str = Field(default_factory=lambda: f"LLM-{uuid.uuid4().hex[:12]}")
    task_id: str
    task_family: str
    capability_id: str | None = None
    capability_version: str | None = None
    phase: ResearchPhase
    usage: TokenUsage = Field(default_factory=TokenUsage)
    latency_ms: float = Field(ge=0)
    success: bool
    error: str | None = None
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TaskCostMetric(BaseModel):
    task_id: str
    task_family: str
    capability_id: str | None = None
    capability_version: str | None = None
    capability_created: bool = False
    capability_reused: bool = False
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    reasoning_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
    llm_call_count: int = Field(default=0, ge=0)
    provider_cost_usd: float | None = Field(default=None, ge=0)
    token_breakdown: dict[str, int | None] = Field(default_factory=dict)
    latency_ms: float = Field(ge=0)
    capability_execution_ms: float | None = Field(default=None, ge=0)
    retry_count: int = Field(default=0, ge=0)
    outcome_status: str
    task_success: bool
    error: str | None = None
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TokenCostSummary(BaseModel):
    task_family: str | None = None
    task_count: int = 0
    successful_task_count: int = 0
    task_success_rate: float | None = None
    capability_creation_count: int = 0
    capability_reuse_count: int = 0
    llm_call_count: int = 0
    token_data_complete: bool = False
    unavailable_token_task_count: int = 0
    cumulative_ceaa_tokens: int | None = None
    average_tokens_per_task: float | None = None
    average_creation_tokens: float | None = None
    average_reuse_tokens: float | None = None
    average_latency_ms: float | None = None
    average_capability_execution_ms: float | None = None
    baseline_tokens_per_task: int | None = None
    cumulative_baseline_tokens: int | None = None
    token_saving: int | None = None
    token_saving_rate: float | None = None
    break_even_reuse_count: int | None = None
    cumulative_provider_cost_usd: float | None = None
    note: str | None = None
