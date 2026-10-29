from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from src.domain.errors import (
    TelemetryConflictError,
    UnknownTraceError,
    UnsupportedTelemetrySchemaError,
)
from src.domain.telemetry import (
    DecisionEvidence,
    ExecutionFailure,
    ExecutionObservation,
    ExecutionTrace,
    FailureCategory,
    FailureStage,
    ObservationKind,
    ObservationOutcome,
    RecoveryAttempt,
    RecoveryStrategy,
    RetryDecision,
    RetryDisposition,
    RoutingDecision,
    SideEffectStatus,
    TraceOutcome,
)
from src.infrastructure.sqlite_telemetry_repository import SqliteTelemetryRepository
from src.infrastructure.sqlite_repository import SqliteCapabilityRepository


_START = datetime(2026, 10, 18, 8, 0, tzinfo=timezone.utc)


def _telemetry_graph():
    trace = ExecutionTrace(
        trace_id="TRACE-contract",
        task_id="TASK-contract",
        task_family="telemetry_contract",
        started_at=_START,
        metadata={"environment": "test"},
    )
    decision = RoutingDecision(
        decision_id="ROUTE-contract",
        trace_id=trace.trace_id,
        depth=0,
        layer="root",
        node_type="capability_router",
        candidate_ids=["CAP-a", "CAP-b"],
        selected_target_id="CAP-a",
        confidence=0.75,
        score=4.2,
        decision_model="deterministic",
        decision_model_version="1",
        policy_version="policy-2026-10",
        evidence=DecisionEvidence(
            selection_criteria=["highest_score"],
            rationale_summary="Selected the strongest eligible candidate",
            evidence_refs=["CAP-a"],
            rejected_alternative_summary="CAP-b scored lower",
            constraints=["active_only"],
            expected_outcome="successful execution",
        ),
        latency_ms=2.5,
        recorded_at=_START + timedelta(milliseconds=2),
    )
    failed_observation = ExecutionObservation(
        observation_id="OBS-failed",
        trace_id=trace.trace_id,
        decision_id=decision.decision_id,
        target_type="capability",
        target_id="CAP-a",
        target_version="1.2.3",
        outcome=ObservationOutcome.FAILED,
        started_at=_START + timedelta(milliseconds=3),
        completed_at=_START + timedelta(milliseconds=13),
        latency_ms=10,
    )
    failure = ExecutionFailure(
        failure_id="FAIL-contract",
        trace_id=trace.trace_id,
        observation_id=failed_observation.observation_id,
        stage=FailureStage.RUNTIME,
        category=FailureCategory.EXECUTION,
        error_code="CAPABILITY_RUNTIME_ERROR",
        exception_type="RuntimeError",
        error_summary="sanitized failure",
        recoverable=True,
        recorded_at=_START + timedelta(milliseconds=14),
    )
    recovery_observation = ExecutionObservation(
        observation_id="OBS-retry",
        trace_id=trace.trace_id,
        decision_id=decision.decision_id,
        parent_observation_id=failed_observation.observation_id,
        kind=ObservationKind.RETRY,
        target_type="capability",
        target_id="CAP-a",
        target_version="1.2.3",
        outcome=ObservationOutcome.SUCCEEDED,
        started_at=_START + timedelta(milliseconds=15),
        completed_at=_START + timedelta(milliseconds=20),
        latency_ms=5,
    )
    recovery = RecoveryAttempt(
        recovery_id="RECOVERY-contract",
        trace_id=trace.trace_id,
        failure_id=failure.failure_id,
        observation_id=recovery_observation.observation_id,
        strategy=RecoveryStrategy.RETRY,
        target_type="capability",
        target_id="CAP-a",
        target_version="1.2.3",
        attempt_number=1,
        outcome=ObservationOutcome.SUCCEEDED,
        retry_decision=RetryDecision(
            disposition=RetryDisposition.RETRY,
            retry_allowed=True,
            retry_count=0,
            max_retries=1,
            side_effect_status=SideEffectStatus.IDEMPOTENT,
            reason_code="TRANSIENT_IDEMPOTENT_FAILURE",
            backoff_ms=0,
        ),
        recorded_at=_START + timedelta(milliseconds=21),
    )
    return trace, decision, failed_observation, failure, recovery_observation, recovery


class TelemetryRepositoryContract:
    """Reusable behavioral contract for SQLite and a future PostgreSQL adapter."""

    def test_round_trip_and_restart(self, repository_factory):
        repository = repository_factory()
        trace, decision, failed, failure, retry, recovery = _telemetry_graph()

        repository.save_trace(trace)
        repository.save_routing_decision(decision)
        repository.save_execution_observation(failed)
        repository.save_execution_failure(failure)
        repository.save_execution_observation(retry)
        repository.save_recovery_attempt(recovery)

        restarted = repository_factory()
        assert restarted.get_trace(trace.trace_id) == trace
        assert restarted.list_routing_decisions(trace.trace_id) == [decision]
        assert restarted.list_execution_observations(trace.trace_id) == [failed, retry]
        assert restarted.list_execution_failures(trace.trace_id) == [failure]
        assert restarted.list_recovery_attempts(trace.trace_id) == [recovery]

    def test_trace_filtering_and_single_completion(self, repository_factory):
        repository = repository_factory()
        first = ExecutionTrace(
            trace_id="TRACE-one",
            task_id="TASK-shared",
            task_family="family-a",
            started_at=_START,
        )
        second = ExecutionTrace(
            trace_id="TRACE-two",
            task_id="TASK-other",
            task_family="family-b",
            started_at=_START + timedelta(seconds=1),
        )
        repository.save_trace(first)
        repository.save_trace(second)

        assert repository.list_traces(task_id="TASK-shared") == [first]
        assert repository.list_traces(task_family="family-b") == [second]

        completed_at = _START + timedelta(seconds=2)
        completed = repository.complete_trace(
            first.trace_id, TraceOutcome.SUCCEEDED, completed_at
        )
        assert completed.final_outcome is TraceOutcome.SUCCEEDED
        assert completed.completed_at == completed_at
        assert repository.get_trace(first.trace_id) == completed

        with pytest.raises(TelemetryConflictError, match="already been completed"):
            repository.complete_trace(first.trace_id, TraceOutcome.FAILED)
        with pytest.raises(UnknownTraceError, match="TRACE-missing"):
            repository.complete_trace("TRACE-missing", TraceOutcome.FAILED)

    def test_duplicate_and_cross_trace_writes_are_rejected(self, repository_factory):
        repository = repository_factory()
        first = ExecutionTrace(
            trace_id="TRACE-first",
            task_id="TASK-first",
            task_family="family",
            started_at=_START,
        )
        second = ExecutionTrace(
            trace_id="TRACE-second",
            task_id="TASK-second",
            task_family="family",
            started_at=_START,
        )
        repository.save_trace(first)
        repository.save_trace(second)
        with pytest.raises(TelemetryConflictError):
            repository.save_trace(first)

        decision = RoutingDecision(
            decision_id="ROUTE-first",
            trace_id=first.trace_id,
            layer="root",
            node_type="router",
            recorded_at=_START,
        )
        repository.save_routing_decision(decision)
        mismatched = ExecutionObservation(
            trace_id=second.trace_id,
            decision_id=decision.decision_id,
            target_type="capability",
            target_id="CAP-x",
            outcome=ObservationOutcome.FAILED,
            started_at=_START,
            completed_at=_START,
        )
        with pytest.raises(TelemetryConflictError):
            repository.save_execution_observation(mismatched)


class TestSqliteTelemetryRepository(TelemetryRepositoryContract):
    @pytest.fixture
    def repository_factory(self, tmp_path):
        database = tmp_path / "telemetry.db"
        return lambda: SqliteTelemetryRepository(str(database))

    def test_schema_version_tables_indexes_and_wal(self, tmp_path):
        database = tmp_path / "schema.db"
        SqliteTelemetryRepository(str(database))

        with sqlite3.connect(database) as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
            indexes = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'index'"
                ).fetchall()
            }
            versions = conn.execute(
                "SELECT version FROM telemetry_schema_migrations ORDER BY version"
            ).fetchall()
            journal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]

        assert {
            "execution_traces",
            "routing_decisions",
            "execution_observations",
            "execution_failures",
            "recovery_attempts",
            "telemetry_schema_migrations",
        } <= tables
        assert {
            "ix_execution_traces_task_id",
            "ix_routing_decisions_trace_time",
            "ix_execution_observations_target",
            "ix_execution_failures_pattern",
            "ix_recovery_attempts_failure",
        } <= indexes
        assert versions == [(1,)]
        assert journal_mode == "wal"

    def test_domain_rejects_naive_timestamps(self):
        with pytest.raises(ValidationError, match="must include a timezone"):
            ExecutionTrace(
                task_id="TASK-naive",
                task_family="time",
                started_at=datetime(2026, 10, 18, 8, 0),
            )

    def test_legacy_routing_payload_uses_extensible_defaults(self):
        legacy = RoutingDecision.model_validate(
            {
                "decision_id": "ROUTE-legacy",
                "trace_id": "TRACE-legacy",
                "layer": "root",
                "node_type": "router",
                "recorded_at": _START,
            }
        )

        assert legacy.contract_version == "1.1"
        assert legacy.task_id is None
        assert legacy.selected_target_version is None
        assert legacy.policy_version is None
        assert legacy.evidence is None

    def test_migration_preserves_existing_capability_data(self, tmp_path):
        database = tmp_path / "existing.db"
        capabilities = SqliteCapabilityRepository(str(database))
        capability, created = capabilities.reserve_for_task("existing", "keep me")
        assert created is True

        SqliteTelemetryRepository(str(database))

        reloaded = SqliteCapabilityRepository(str(database)).get(capability.capability_id)
        assert reloaded == capability

    def test_newer_schema_version_is_rejected(self, tmp_path):
        database = tmp_path / "future.db"
        with sqlite3.connect(database) as conn:
            conn.execute(
                """CREATE TABLE telemetry_schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                )"""
            )
            conn.execute(
                "INSERT INTO telemetry_schema_migrations (version, applied_at) VALUES (?, ?)",
                (999, _START.isoformat()),
            )

        with pytest.raises(UnsupportedTelemetrySchemaError, match="999"):
            SqliteTelemetryRepository(str(database))
