from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from src.domain.telemetry import (
    ExecutionFailure,
    ExecutionObservation,
    ExecutionTrace,
    RecoveryAttempt,
    RoutingDecision,
    TraceOutcome,
)


class TelemetryRepository(ABC):
    """Backend-neutral persistence contract for execution telemetry."""

    @abstractmethod
    def save_trace(self, trace: ExecutionTrace) -> None: ...

    @abstractmethod
    def complete_trace(
        self,
        trace_id: str,
        outcome: TraceOutcome,
        completed_at: datetime | None = None,
    ) -> ExecutionTrace: ...

    @abstractmethod
    def get_trace(self, trace_id: str) -> ExecutionTrace | None: ...

    @abstractmethod
    def list_traces(
        self,
        task_id: str | None = None,
        task_family: str | None = None,
    ) -> list[ExecutionTrace]: ...

    @abstractmethod
    def save_routing_decision(self, decision: RoutingDecision) -> None: ...

    @abstractmethod
    def list_routing_decisions(self, trace_id: str) -> list[RoutingDecision]: ...

    @abstractmethod
    def save_execution_observation(self, observation: ExecutionObservation) -> None: ...

    @abstractmethod
    def list_execution_observations(self, trace_id: str) -> list[ExecutionObservation]: ...

    @abstractmethod
    def save_execution_failure(self, failure: ExecutionFailure) -> None: ...

    @abstractmethod
    def list_execution_failures(self, trace_id: str) -> list[ExecutionFailure]: ...

    @abstractmethod
    def save_recovery_attempt(self, attempt: RecoveryAttempt) -> None: ...

    @abstractmethod
    def list_recovery_attempts(self, trace_id: str) -> list[RecoveryAttempt]: ...
