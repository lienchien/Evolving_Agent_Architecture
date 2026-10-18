from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from src.domain.errors import (
    TelemetryConflictError,
    UnknownTraceError,
    UnsupportedTelemetrySchemaError,
)
from src.domain.telemetry import (
    ExecutionFailure,
    ExecutionObservation,
    ExecutionTrace,
    RecoveryAttempt,
    RoutingDecision,
    TraceOutcome,
)
from src.interfaces.telemetry_repository import TelemetryRepository


_TELEMETRY_SCHEMA_VERSION = 1
_ModelT = TypeVar("_ModelT", bound=BaseModel)


class SqliteTelemetryRepository(TelemetryRepository):
    """SQLite telemetry adapter.

    Domain and service layers depend only on ``TelemetryRepository``. JSON
    encoding, SQLite pragmas, SQL syntax and migrations remain inside this
    adapter so a PostgreSQL implementation can replace it later.
    """

    def __init__(self, db_path: str = "capability_library.db") -> None:
        self._db_path = db_path
        parent = Path(db_path).parent
        if str(parent) not in ("", "."):
            parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self._db_path, timeout=15.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA busy_timeout = 15000")
            with conn:
                yield conn
        except sqlite3.IntegrityError as exc:
            raise TelemetryConflictError(
                "Telemetry uniqueness or correlation constraint conflict"
            ) from exc
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                """CREATE TABLE IF NOT EXISTS telemetry_schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                )"""
            )
            applied = {
                row["version"]
                for row in conn.execute(
                    "SELECT version FROM telemetry_schema_migrations"
                ).fetchall()
            }
            newer_versions = [
                version for version in applied if version > _TELEMETRY_SCHEMA_VERSION
            ]
            if newer_versions:
                raise UnsupportedTelemetrySchemaError(
                    "Telemetry schema version "
                    f"{max(newer_versions)} is newer than supported version "
                    f"{_TELEMETRY_SCHEMA_VERSION}"
                )
            if _TELEMETRY_SCHEMA_VERSION not in applied:
                self._apply_v1(conn)
                conn.execute(
                    "INSERT INTO telemetry_schema_migrations (version, applied_at) VALUES (?, ?)",
                    (_TELEMETRY_SCHEMA_VERSION, datetime.now(timezone.utc).isoformat()),
                )

    @staticmethod
    def _apply_v1(conn: sqlite3.Connection) -> None:
        statements = (
            """CREATE TABLE IF NOT EXISTS execution_traces (
                trace_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                task_family TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                final_outcome TEXT,
                data TEXT NOT NULL,
                CHECK ((completed_at IS NULL AND final_outcome IS NULL)
                    OR (completed_at IS NOT NULL AND final_outcome IS NOT NULL))
            )""",
            "CREATE INDEX IF NOT EXISTS ix_execution_traces_task_id "
            "ON execution_traces(task_id)",
            "CREATE INDEX IF NOT EXISTS ix_execution_traces_family_started "
            "ON execution_traces(task_family, started_at)",
            """CREATE TABLE IF NOT EXISTS routing_decisions (
                decision_id TEXT PRIMARY KEY,
                trace_id TEXT NOT NULL REFERENCES execution_traces(trace_id),
                parent_decision_id TEXT,
                depth INTEGER NOT NULL CHECK (depth >= 0),
                layer TEXT NOT NULL,
                node_type TEXT NOT NULL,
                candidate_count INTEGER NOT NULL CHECK (candidate_count >= 0),
                selected_target_id TEXT,
                confidence REAL CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
                score REAL,
                latency_ms REAL CHECK (latency_ms IS NULL OR latency_ms >= 0),
                recorded_at TEXT NOT NULL,
                data TEXT NOT NULL,
                UNIQUE(decision_id, trace_id),
                FOREIGN KEY (parent_decision_id, trace_id)
                    REFERENCES routing_decisions(decision_id, trace_id)
            )""",
            "CREATE INDEX IF NOT EXISTS ix_routing_decisions_trace_time "
            "ON routing_decisions(trace_id, recorded_at)",
            "CREATE INDEX IF NOT EXISTS ix_routing_decisions_selected "
            "ON routing_decisions(selected_target_id, recorded_at)",
            """CREATE TABLE IF NOT EXISTS execution_observations (
                observation_id TEXT PRIMARY KEY,
                trace_id TEXT NOT NULL REFERENCES execution_traces(trace_id),
                decision_id TEXT,
                parent_observation_id TEXT,
                kind TEXT NOT NULL,
                target_type TEXT NOT NULL,
                target_id TEXT NOT NULL,
                outcome TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT NOT NULL,
                latency_ms REAL CHECK (latency_ms IS NULL OR latency_ms >= 0),
                data TEXT NOT NULL,
                UNIQUE(observation_id, trace_id),
                FOREIGN KEY (decision_id, trace_id)
                    REFERENCES routing_decisions(decision_id, trace_id),
                FOREIGN KEY (parent_observation_id, trace_id)
                    REFERENCES execution_observations(observation_id, trace_id)
            )""",
            "CREATE INDEX IF NOT EXISTS ix_execution_observations_trace_time "
            "ON execution_observations(trace_id, started_at)",
            "CREATE INDEX IF NOT EXISTS ix_execution_observations_target "
            "ON execution_observations(target_type, target_id, started_at)",
            "CREATE INDEX IF NOT EXISTS ix_execution_observations_outcome "
            "ON execution_observations(outcome, started_at)",
            """CREATE TABLE IF NOT EXISTS execution_failures (
                failure_id TEXT PRIMARY KEY,
                trace_id TEXT NOT NULL REFERENCES execution_traces(trace_id),
                observation_id TEXT NOT NULL,
                stage TEXT NOT NULL,
                category TEXT NOT NULL,
                error_code TEXT,
                exception_type TEXT,
                recoverable INTEGER CHECK (recoverable IS NULL OR recoverable IN (0, 1)),
                recorded_at TEXT NOT NULL,
                data TEXT NOT NULL,
                UNIQUE(failure_id, trace_id),
                FOREIGN KEY (observation_id, trace_id)
                    REFERENCES execution_observations(observation_id, trace_id)
            )""",
            "CREATE INDEX IF NOT EXISTS ix_execution_failures_trace_time "
            "ON execution_failures(trace_id, recorded_at)",
            "CREATE INDEX IF NOT EXISTS ix_execution_failures_pattern "
            "ON execution_failures(category, exception_type, recorded_at)",
            """CREATE TABLE IF NOT EXISTS recovery_attempts (
                recovery_id TEXT PRIMARY KEY,
                trace_id TEXT NOT NULL REFERENCES execution_traces(trace_id),
                failure_id TEXT NOT NULL,
                observation_id TEXT NOT NULL,
                strategy TEXT NOT NULL,
                target_type TEXT NOT NULL,
                target_id TEXT NOT NULL,
                attempt_number INTEGER NOT NULL CHECK (attempt_number >= 1),
                outcome TEXT NOT NULL,
                recorded_at TEXT NOT NULL,
                data TEXT NOT NULL,
                FOREIGN KEY (failure_id, trace_id)
                    REFERENCES execution_failures(failure_id, trace_id),
                FOREIGN KEY (observation_id, trace_id)
                    REFERENCES execution_observations(observation_id, trace_id)
            )""",
            "CREATE INDEX IF NOT EXISTS ix_recovery_attempts_trace_time "
            "ON recovery_attempts(trace_id, recorded_at)",
            "CREATE INDEX IF NOT EXISTS ix_recovery_attempts_failure "
            "ON recovery_attempts(failure_id, attempt_number)",
        )
        for statement in statements:
            conn.execute(statement)

    @staticmethod
    def _models(rows: list[sqlite3.Row], model: type[_ModelT]) -> list[_ModelT]:
        return [model.model_validate_json(row["data"]) for row in rows]

    def save_trace(self, trace: ExecutionTrace) -> None:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO execution_traces
                (trace_id, task_id, task_family, started_at, completed_at, final_outcome, data)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    trace.trace_id,
                    trace.task_id,
                    trace.task_family,
                    trace.started_at.isoformat(),
                    trace.completed_at.isoformat() if trace.completed_at else None,
                    trace.final_outcome.value if trace.final_outcome else None,
                    trace.model_dump_json(),
                ),
            )

    def complete_trace(
        self,
        trace_id: str,
        outcome: TraceOutcome,
        completed_at: datetime | None = None,
    ) -> ExecutionTrace:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT data FROM execution_traces WHERE trace_id = ?", (trace_id,)
            ).fetchone()
            if row is None:
                raise UnknownTraceError(f"Unknown execution trace: {trace_id}")
            trace = ExecutionTrace.model_validate_json(row["data"])
            if trace.final_outcome is not None:
                raise TelemetryConflictError(
                    f"Execution trace {trace_id} has already been completed"
                )
            completed = ExecutionTrace.model_validate(
                {
                    **trace.model_dump(),
                    "completed_at": completed_at or datetime.now(timezone.utc),
                    "final_outcome": outcome,
                }
            )
            cursor = conn.execute(
                """UPDATE execution_traces
                SET completed_at = ?, final_outcome = ?, data = ?
                WHERE trace_id = ? AND final_outcome IS NULL""",
                (
                    completed.completed_at.isoformat(),
                    completed.final_outcome.value,
                    completed.model_dump_json(),
                    trace_id,
                ),
            )
            if cursor.rowcount != 1:
                raise TelemetryConflictError(
                    f"Execution trace {trace_id} has already been completed"
                )
        return completed

    def get_trace(self, trace_id: str) -> ExecutionTrace | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT data FROM execution_traces WHERE trace_id = ?", (trace_id,)
            ).fetchone()
        return ExecutionTrace.model_validate_json(row["data"]) if row else None

    def list_traces(
        self,
        task_id: str | None = None,
        task_family: str | None = None,
    ) -> list[ExecutionTrace]:
        clauses: list[str] = []
        params: list[str] = []
        if task_id is not None:
            clauses.append("task_id = ?")
            params.append(task_id)
        if task_family is not None:
            clauses.append("task_family = ?")
            params.append(task_family)
        query = "SELECT data FROM execution_traces"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY started_at, trace_id"
        with self._connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return self._models(rows, ExecutionTrace)

    def save_routing_decision(self, decision: RoutingDecision) -> None:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO routing_decisions
                (decision_id, trace_id, parent_decision_id, depth, layer, node_type,
                 candidate_count, selected_target_id, confidence, score, latency_ms,
                 recorded_at, data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    decision.decision_id,
                    decision.trace_id,
                    decision.parent_decision_id,
                    decision.depth,
                    decision.layer,
                    decision.node_type,
                    len(decision.candidate_ids),
                    decision.selected_target_id,
                    decision.confidence,
                    decision.score,
                    decision.latency_ms,
                    decision.recorded_at.isoformat(),
                    decision.model_dump_json(),
                ),
            )

    def list_routing_decisions(self, trace_id: str) -> list[RoutingDecision]:
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT data FROM routing_decisions WHERE trace_id = ?
                ORDER BY recorded_at, decision_id""",
                (trace_id,),
            ).fetchall()
        return self._models(rows, RoutingDecision)

    def save_execution_observation(self, observation: ExecutionObservation) -> None:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO execution_observations
                (observation_id, trace_id, decision_id, parent_observation_id, kind,
                 target_type, target_id, outcome, started_at, completed_at, latency_ms, data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    observation.observation_id,
                    observation.trace_id,
                    observation.decision_id,
                    observation.parent_observation_id,
                    observation.kind.value,
                    observation.target_type,
                    observation.target_id,
                    observation.outcome.value,
                    observation.started_at.isoformat(),
                    observation.completed_at.isoformat(),
                    observation.latency_ms,
                    observation.model_dump_json(),
                ),
            )

    def list_execution_observations(self, trace_id: str) -> list[ExecutionObservation]:
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT data FROM execution_observations WHERE trace_id = ?
                ORDER BY started_at, observation_id""",
                (trace_id,),
            ).fetchall()
        return self._models(rows, ExecutionObservation)

    def save_execution_failure(self, failure: ExecutionFailure) -> None:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO execution_failures
                (failure_id, trace_id, observation_id, stage, category, error_code,
                 exception_type, recoverable, recorded_at, data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    failure.failure_id,
                    failure.trace_id,
                    failure.observation_id,
                    failure.stage.value,
                    failure.category.value,
                    failure.error_code,
                    failure.exception_type,
                    None if failure.recoverable is None else int(failure.recoverable),
                    failure.recorded_at.isoformat(),
                    failure.model_dump_json(),
                ),
            )

    def list_execution_failures(self, trace_id: str) -> list[ExecutionFailure]:
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT data FROM execution_failures WHERE trace_id = ?
                ORDER BY recorded_at, failure_id""",
                (trace_id,),
            ).fetchall()
        return self._models(rows, ExecutionFailure)

    def save_recovery_attempt(self, attempt: RecoveryAttempt) -> None:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO recovery_attempts
                (recovery_id, trace_id, failure_id, observation_id, strategy,
                 target_type, target_id, attempt_number, outcome, recorded_at, data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    attempt.recovery_id,
                    attempt.trace_id,
                    attempt.failure_id,
                    attempt.observation_id,
                    attempt.strategy.value,
                    attempt.target_type,
                    attempt.target_id,
                    attempt.attempt_number,
                    attempt.outcome.value,
                    attempt.recorded_at.isoformat(),
                    attempt.model_dump_json(),
                ),
            )

    def list_recovery_attempts(self, trace_id: str) -> list[RecoveryAttempt]:
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT data FROM recovery_attempts WHERE trace_id = ?
                ORDER BY recorded_at, recovery_id""",
                (trace_id,),
            ).fetchall()
        return self._models(rows, RecoveryAttempt)
