from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.telemetry import FailureContext, RetryDecision, SideEffectStatus


class RetryPolicyInterface(ABC):
    @abstractmethod
    def decide(
        self,
        context: FailureContext,
        *,
        retry_count: int,
        max_retries: int,
        side_effect_status: SideEffectStatus,
        remaining_time_ms: int | None = None,
        remaining_cost_usd: float | None = None,
    ) -> RetryDecision: ...
