from __future__ import annotations

from src.domain.telemetry import (
    FailureContext,
    RetryDecision,
    RetryDisposition,
    SideEffectStatus,
)
from src.interfaces.retry_policy import RetryPolicyInterface


class BoundedRetryPolicy(RetryPolicyInterface):
    """Fail-closed retry policy for explicitly idempotent transient operations."""

    def __init__(self, *, hard_max_retries: int = 3, base_backoff_ms: int = 0) -> None:
        if hard_max_retries < 0:
            raise ValueError("hard_max_retries cannot be negative")
        if base_backoff_ms < 0:
            raise ValueError("base_backoff_ms cannot be negative")
        self._hard_max_retries = hard_max_retries
        self._base_backoff_ms = base_backoff_ms

    def decide(
        self,
        context: FailureContext,
        *,
        retry_count: int,
        max_retries: int,
        side_effect_status: SideEffectStatus,
        remaining_time_ms: int | None = None,
        remaining_cost_usd: float | None = None,
    ) -> RetryDecision:
        bounded_max = min(max(max_retries, 0), self._hard_max_retries)
        common = {
            "retry_count": retry_count,
            "max_retries": bounded_max,
            "side_effect_status": side_effect_status,
            "recoverable": context.recoverable,
            "remaining_time_ms": remaining_time_ms,
            "remaining_cost_usd": remaining_cost_usd,
        }
        if remaining_time_ms == 0 or remaining_cost_usd == 0:
            return RetryDecision(
                disposition=RetryDisposition.EXHAUSTED,
                retry_allowed=False,
                reason_code="RETRY_BUDGET_EXHAUSTED",
                **common,
            )
        if side_effect_status is not SideEffectStatus.IDEMPOTENT:
            return RetryDecision(
                disposition=RetryDisposition.BLOCKED,
                retry_allowed=False,
                reason_code=(
                    "NON_IDEMPOTENT_OPERATION"
                    if side_effect_status is SideEffectStatus.NON_IDEMPOTENT
                    else "UNKNOWN_SIDE_EFFECTS"
                ),
                **common,
            )
        if context.recoverable is not True:
            return RetryDecision(
                disposition=RetryDisposition.BLOCKED,
                retry_allowed=False,
                reason_code="FAILURE_NOT_RETRYABLE",
                **common,
            )
        if retry_count >= bounded_max:
            return RetryDecision(
                disposition=RetryDisposition.EXHAUSTED,
                retry_allowed=False,
                reason_code="RETRY_LIMIT_EXHAUSTED",
                **common,
            )
        return RetryDecision(
            disposition=RetryDisposition.RETRY,
            retry_allowed=True,
            reason_code="TRANSIENT_IDEMPOTENT_FAILURE",
            backoff_ms=self._base_backoff_ms * (2**retry_count),
            **common,
        )
