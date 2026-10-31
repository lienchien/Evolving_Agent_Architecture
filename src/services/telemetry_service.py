from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable

from src.domain.errors import UnknownTraceError
from src.domain.telemetry import (
    DecisionEvidence,
    ExecutionFailure,
    ExecutionObservation,
    ExecutionTrace,
    ExecutionTraceDetail,
    FailureCategory,
    FailureRecurrence,
    FailureStage,
    ObservationKind,
    ObservationOutcome,
    RecoveryAttempt,
    RecoveryStrategy,
    RetryDecision,
    RoutingDecision,
    TelemetrySummary,
    TraceOutcome,
)
from src.interfaces.telemetry_repository import TelemetryRepository


logger = logging.getLogger(__name__)


class TelemetryService:
    """Records operational history without changing the primary task outcome."""

    def __init__(self, repository: TelemetryRepository) -> None:
        self._repository = repository
        self._instrumentation_failure_count = 0
        self._counter_lock = Lock()

    @property
    def instrumentation_failure_count(self) -> int:
        with self._counter_lock:
            return self._instrumentation_failure_count

    def _record_instrumentation_failure(self, operation: str) -> None:
        with self._counter_lock:
            self._instrumentation_failure_count += 1
        logger.exception("Telemetry instrumentation failed during %s", operation)

    def _write(self, operation: str, writer: Callable[[], object]) -> None:
        try:
            writer()
        except Exception:
            self._record_instrumentation_failure(operation)

    def start_trace(self, *, task_id: str, task_family: str) -> ExecutionTrace:
        trace = ExecutionTrace(task_id=task_id, task_family=task_family)
        self._write("save_trace", lambda: self._repository.save_trace(trace))
        return trace

    def complete_trace(self, trace_id: str, outcome: TraceOutcome) -> None:
        self._write(
            "complete_trace",
            lambda: self._repository.complete_trace(trace_id, outcome),
        )

    def record_routing_decision(
        self,
        *,
        trace_id: str,
        task_id: str | None,
        candidate_ids: list[str],
        selected_target_id: str | None,
        selected_target_version: str | None,
        latency_ms: float,
        parent_decision_id: str | None = None,
        depth: int = 0,
        layer: str = "task",
        node_type: str = "capability_router",
        policy_version: str | None = None,
        fallback_reason: str | None = None,
        override_reason: str | None = None,
        evidence: DecisionEvidence | None = None,
    ) -> RoutingDecision:
        decision = RoutingDecision(
            trace_id=trace_id,
            task_id=task_id,
            parent_decision_id=parent_decision_id,
            depth=depth,
            layer=layer,
            node_type=node_type,
            candidate_ids=candidate_ids,
            selected_target_id=selected_target_id,
            selected_target_version=selected_target_version,
            latency_ms=latency_ms,
            decision_model="deterministic",
            decision_model_version="capability-router-v1",
            policy_version=policy_version,
            fallback_reason=fallback_reason,
            override_reason=override_reason,
            evidence=evidence,
        )
        self._write(
            "save_routing_decision",
            lambda: self._repository.save_routing_decision(decision),
        )
        return decision

    def record_observation(
        self,
        *,
        trace_id: str,
        target_type: str,
        target_id: str,
        target_version: str | None,
        outcome: ObservationOutcome,
        started_at: datetime,
        completed_at: datetime,
        latency_ms: float,
        decision_id: str | None = None,
        parent_observation_id: str | None = None,
        kind: ObservationKind = ObservationKind.EXECUTION,
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionObservation:
        observation = ExecutionObservation(
            trace_id=trace_id,
            decision_id=decision_id,
            parent_observation_id=parent_observation_id,
            kind=kind,
            target_type=target_type,
            target_id=target_id,
            target_version=target_version,
            outcome=outcome,
            started_at=started_at,
            completed_at=completed_at,
            latency_ms=latency_ms,
            metadata=metadata or {},
        )
        self._write(
            "save_execution_observation",
            lambda: self._repository.save_execution_observation(observation),
        )
        return observation

    def record_failure(
        self,
        *,
        trace_id: str,
        observation_id: str,
        stage: FailureStage,
        category: FailureCategory,
        error_code: str,
        summary: str,
        exception: Exception | None = None,
        recoverable: bool | None = None,
    ) -> ExecutionFailure:
        failure = ExecutionFailure(
            trace_id=trace_id,
            observation_id=observation_id,
            stage=stage,
            category=category,
            error_code=error_code,
            exception_type=type(exception).__name__ if exception is not None else None,
            error_summary=summary,
            recoverable=recoverable,
        )
        self._write(
            "save_execution_failure",
            lambda: self._repository.save_execution_failure(failure),
        )
        return failure

    def record_recovery_attempt(
        self,
        *,
        trace_id: str,
        failure_id: str,
        observation_id: str,
        strategy: RecoveryStrategy,
        target_type: str,
        target_id: str,
        target_version: str | None,
        attempt_number: int,
        outcome: ObservationOutcome,
        retry_decision: RetryDecision | None = None,
    ) -> RecoveryAttempt:
        attempt = RecoveryAttempt(
            trace_id=trace_id,
            failure_id=failure_id,
            observation_id=observation_id,
            strategy=strategy,
            target_type=target_type,
            target_id=target_id,
            target_version=target_version,
            attempt_number=attempt_number,
            outcome=outcome,
            retry_decision=retry_decision,
        )
        self._write(
            "save_recovery_attempt",
            lambda: self._repository.save_recovery_attempt(attempt),
        )
        return attempt

    def record_unhandled_failure(
        self, *, trace_id: str, task_id: str, exception: Exception
    ) -> None:
        try:
            if self._repository.list_execution_failures(trace_id):
                return
        except Exception:
            self._record_instrumentation_failure("check_existing_failures")
            return

        now = datetime.now(timezone.utc)
        observation = self.record_observation(
            trace_id=trace_id,
            target_type="task",
            target_id=task_id,
            target_version=None,
            outcome=ObservationOutcome.FAILED,
            started_at=now,
            completed_at=now,
            latency_ms=0,
        )
        self.record_failure(
            trace_id=trace_id,
            observation_id=observation.observation_id,
            stage=FailureStage.RUNTIME,
            category=FailureCategory.UNKNOWN,
            error_code="UNHANDLED_TASK_FAILURE",
            summary="Task failed before a more specific failure could be recorded",
            exception=exception,
        )

    def list_traces(
        self,
        *,
        task_id: str | None = None,
        task_family: str | None = None,
        capability_id: str | None = None,
        target_id: str | None = None,
        failure_category: FailureCategory | None = None,
        exception_type: str | None = None,
        outcome: TraceOutcome | None = None,
        started_after: datetime | None = None,
        started_before: datetime | None = None,
    ) -> list[ExecutionTrace]:
        for value in (started_after, started_before):
            if value is not None and (value.tzinfo is None or value.utcoffset() is None):
                raise ValueError("telemetry time filters must include a timezone")
        traces = self._repository.list_traces(task_id=task_id, task_family=task_family)
        if outcome is not None:
            traces = [trace for trace in traces if trace.final_outcome is outcome]
        if started_after is not None:
            traces = [trace for trace in traces if trace.started_at >= started_after]
        if started_before is not None:
            traces = [trace for trace in traces if trace.started_at <= started_before]
        if (
            capability_id is None
            and target_id is None
            and failure_category is None
            and exception_type is None
        ):
            return traces

        filtered: list[ExecutionTrace] = []
        for trace in traces:
            decisions = self._repository.list_routing_decisions(trace.trace_id)
            observations = self._repository.list_execution_observations(trace.trace_id)
            failures = self._repository.list_execution_failures(trace.trace_id)
            if capability_id is not None and not (
                any(decision.selected_target_id == capability_id for decision in decisions)
                or any(
                    observation.target_id == capability_id
                    and observation.target_type.startswith("capability")
                    for observation in observations
                )
            ):
                continue
            if target_id is not None and not (
                any(decision.selected_target_id == target_id for decision in decisions)
                or any(observation.target_id == target_id for observation in observations)
            ):
                continue
            if exception_type is not None and not any(
                failure.exception_type == exception_type for failure in failures
            ):
                continue
            if failure_category is not None and not any(
                failure.category is failure_category for failure in failures
            ):
                continue
            filtered.append(trace)
        return filtered

    def get_trace_detail(self, trace_id: str) -> ExecutionTraceDetail:
        trace = self._repository.get_trace(trace_id)
        if trace is None:
            raise UnknownTraceError(f"Unknown execution trace: {trace_id}")
        return ExecutionTraceDetail(
            trace=trace,
            routing_decisions=self._repository.list_routing_decisions(trace_id),
            observations=self._repository.list_execution_observations(trace_id),
            failures=self._repository.list_execution_failures(trace_id),
            recovery_attempts=self._repository.list_recovery_attempts(trace_id),
        )

    def summarize(
        self,
        *,
        task_id: str | None = None,
        task_family: str | None = None,
        capability_id: str | None = None,
        target_id: str | None = None,
        failure_category: FailureCategory | None = None,
        exception_type: str | None = None,
        outcome: TraceOutcome | None = None,
        started_after: datetime | None = None,
        started_before: datetime | None = None,
    ) -> TelemetrySummary:
        traces = self.list_traces(
            task_id=task_id,
            task_family=task_family,
            capability_id=capability_id,
            target_id=target_id,
            failure_category=failure_category,
            exception_type=exception_type,
            outcome=outcome,
            started_after=started_after,
            started_before=started_before,
        )
        outcomes = Counter(trace.final_outcome for trace in traces)
        completed_count = sum(count for outcome, count in outcomes.items() if outcome is not None)
        decisions: list[RoutingDecision] = []
        observations: list[ExecutionObservation] = []
        failures: list[ExecutionFailure] = []
        recovery_attempts: list[RecoveryAttempt] = []
        missing_event_count = 0
        missing_event_trace_count = 0
        for trace in traces:
            trace_decisions = self._repository.list_routing_decisions(trace.trace_id)
            trace_observations = self._repository.list_execution_observations(
                trace.trace_id
            )
            trace_failures = self._repository.list_execution_failures(trace.trace_id)
            trace_recovery_attempts = self._repository.list_recovery_attempts(
                trace.trace_id
            )
            decisions.extend(trace_decisions)
            observations.extend(trace_observations)
            failures.extend(trace_failures)
            recovery_attempts.extend(trace_recovery_attempts)

            trace_missing_events = 0
            if trace.final_outcome is not None and not trace_observations:
                trace_missing_events += 1
            if (
                trace.final_outcome is not None
                and trace.final_outcome is not TraceOutcome.FAILED
                and not trace_decisions
            ):
                trace_missing_events += 1
            if trace_missing_events:
                missing_event_trace_count += 1
                missing_event_count += trace_missing_events

        patterns = Counter(
            (
                failure.stage,
                failure.category,
                failure.error_code,
                failure.exception_type,
            )
            for failure in failures
        )
        recurrences = [
            FailureRecurrence(
                stage=stage,
                category=category,
                error_code=error_code,
                exception_type=exception_type,
                count=count,
            )
            for (stage, category, error_code, exception_type), count in sorted(
                patterns.items(),
                key=lambda item: (
                    -item[1],
                    item[0][0].value,
                    item[0][1].value,
                    item[0][2] or "",
                    item[0][3] or "",
                ),
            )
        ]
        succeeded = outcomes[TraceOutcome.SUCCEEDED]
        failed = outcomes[TraceOutcome.FAILED]
        retry_attempts = [
            attempt
            for attempt in recovery_attempts
            if attempt.strategy is RecoveryStrategy.RETRY
        ]
        successful_retries = sum(
            attempt.outcome is ObservationOutcome.SUCCEEDED
            for attempt in retry_attempts
        )
        return TelemetrySummary(
            task_family=task_family,
            trace_count=len(traces),
            completed_trace_count=completed_count,
            in_progress_trace_count=outcomes[None],
            succeeded_trace_count=succeeded,
            failed_trace_count=failed,
            partial_trace_count=outcomes[TraceOutcome.PARTIAL],
            cancelled_trace_count=outcomes[TraceOutcome.CANCELLED],
            success_rate=succeeded / completed_count if completed_count else None,
            failure_rate=failed / completed_count if completed_count else None,
            routing_decision_count=len(decisions),
            observation_count=len(observations),
            failure_count=len(failures),
            wrong_selection_proxy_count=sum(
                failure.category is FailureCategory.WRONG_SELECTION
                for failure in failures
            ),
            retry_observation_count=sum(
                observation.kind is ObservationKind.RETRY for observation in observations
            ),
            fallback_observation_count=sum(
                observation.kind is ObservationKind.FALLBACK for observation in observations
            ),
            recovery_attempt_count=len(recovery_attempts),
            retry_recovery_rate=(
                successful_retries / len(retry_attempts) if retry_attempts else None
            ),
            missing_event_count=missing_event_count,
            missing_event_trace_count=missing_event_trace_count,
            instrumentation_failure_count=self.instrumentation_failure_count,
            failure_recurrences=recurrences,
        )
