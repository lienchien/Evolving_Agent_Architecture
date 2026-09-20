from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from src.domain.capability import Capability, CapabilityStatus, Implementation
from src.domain.errors import CapabilityConflictError
from src.domain.approval import ApprovalRecord
from src.domain.report import TestReport
from src.interfaces.repository import CapabilityRepository


# A family has one current generation/review/active slot. Terminal versions
# remain in the registry without blocking a replacement.
_OPEN_STATUSES = "'draft','candidate','validating','testing','tested','pending_approval','approved','active'"


class SqliteCapabilityRepository(CapabilityRepository):
    def __init__(self, db_path: str = "capability_library.db") -> None:
        self._db_path = db_path
        parent = Path(db_path).parent
        if str(parent) not in ("", "."):
            parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self._db_path, timeout=15.0)
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            with conn:
                yield conn
        except sqlite3.IntegrityError as exc:
            raise CapabilityConflictError("Capability constraint conflict") from exc
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS capabilities (
                    capability_id TEXT PRIMARY KEY,
                    task_family TEXT NOT NULL,
                    status TEXT NOT NULL,
                    data TEXT NOT NULL,
                    revision INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            columns = {row[1] for row in conn.execute("PRAGMA table_info(capabilities)")}
            if "revision" not in columns:
                conn.execute("ALTER TABLE capabilities ADD COLUMN revision INTEGER NOT NULL DEFAULT 0")
            duplicates = conn.execute(
                f"SELECT task_family FROM capabilities WHERE status IN ({_OPEN_STATUSES}) "
                "GROUP BY task_family HAVING COUNT(*) > 1 LIMIT 1"
            ).fetchone()
            if duplicates:
                raise CapabilityConflictError(
                    "Existing database has multiple open capabilities for a task family; "
                    "resolve them explicitly before starting the upgraded service"
                )
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_capabilities_open_family "
                f"ON capabilities(task_family) WHERE status IN ({_OPEN_STATUSES})"
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS test_reports (
                    capability_id TEXT NOT NULL REFERENCES capabilities(capability_id),
                    capability_version TEXT NOT NULL,
                    data TEXT NOT NULL,
                    PRIMARY KEY (capability_id, capability_version)
                )"""
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS approval_records (
                    approval_id TEXT PRIMARY KEY,
                    capability_id TEXT NOT NULL REFERENCES capabilities(capability_id),
                    data TEXT NOT NULL
                )"""
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS audit_entries (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT NOT NULL
                )"""
            )

    def create(self, capability: Capability) -> None:
        with self._connect() as conn:
            self._insert(conn, capability)

    @staticmethod
    def _insert(conn: sqlite3.Connection, capability: Capability) -> None:
        conn.execute(
            """
            INSERT INTO capabilities (capability_id, task_family, status, data, revision)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                capability.capability_id,
                capability.task_family,
                capability.status.value,
                capability.model_dump_json(),
                capability.revision,
            ),
        )

    def reserve_for_task(self, task_family: str, description: str) -> tuple[Capability, bool]:
        # Serialize only the short reservation transaction, never generation or
        # subprocess execution. This coordinates separate processes as well.
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                f"SELECT data FROM capabilities WHERE task_family = ? AND status IN ({_OPEN_STATUSES})",
                (task_family,),
            ).fetchone()
            if row is not None:
                return Capability.model_validate_json(row[0]), False
            capability = Capability(
                name=task_family, task_family=task_family, description=description,
                implementation=Implementation(code=""),
            )
            self._insert(conn, capability)
            return capability, True

    def save(
        self, capability: Capability, *, approval: ApprovalRecord | None = None,
        audit: dict | None = None,
    ) -> None:
        updated = capability.model_copy(deep=True)
        updated.revision += 1
        updated.updated_at = datetime.now(timezone.utc)
        with self._connect() as conn:
            cursor = conn.execute(
                """UPDATE capabilities SET task_family = ?, status = ?, data = ?, revision = ?
                WHERE capability_id = ? AND revision = ?""",
                (updated.task_family, updated.status.value, updated.model_dump_json(),
                 updated.revision, updated.capability_id, capability.revision),
            )
            if cursor.rowcount != 1:
                raise CapabilityConflictError(
                    f"stale capability {capability.capability_id}; reload before retrying"
                )
            if approval is not None:
                if (approval.capability_id != capability.capability_id
                        or approval.capability_version != capability.capability_version):
                    raise ValueError("Approval must refer to the capability being updated")
                conn.execute(
                    "INSERT INTO approval_records (approval_id, capability_id, data) VALUES (?, ?, ?)",
                    (approval.approval_id, approval.capability_id, approval.model_dump_json()),
                )
            if audit is not None:
                self._insert_audit(conn, audit)
        capability.revision = updated.revision
        capability.updated_at = updated.updated_at

    @staticmethod
    def _insert_audit(conn: sqlite3.Connection, entry: dict) -> None:
        conn.execute("INSERT INTO audit_entries (data) VALUES (?)", (json.dumps(entry),))

    def record_audit(self, entry: dict) -> None:
        with self._connect() as conn:
            self._insert_audit(conn, entry)

    def list_audit(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT data FROM audit_entries ORDER BY sequence").fetchall()
        return [json.loads(row[0]) for row in rows]

    def list_approvals(self) -> list[ApprovalRecord]:
        with self._connect() as conn:
            rows = conn.execute("SELECT data FROM approval_records ORDER BY rowid").fetchall()
        return [ApprovalRecord.model_validate_json(row[0]) for row in rows]

    def save_report(self, report: TestReport) -> None:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO test_reports (capability_id, capability_version, data)
                VALUES (?, ?, ?) ON CONFLICT(capability_id, capability_version)
                DO UPDATE SET data = excluded.data""",
                (report.capability_id, report.capability_version, report.model_dump_json()),
            )

    def get_report(self, capability_id: str) -> TestReport | None:
        with self._connect() as conn:
            row = conn.execute(
                """SELECT r.data FROM test_reports r JOIN capabilities c
                ON r.capability_id = c.capability_id
                AND r.capability_version = json_extract(c.data, '$.capability_version')
                WHERE c.capability_id = ?""", (capability_id,),
            ).fetchone()
        return TestReport.model_validate_json(row[0]) if row else None

    def get(self, capability_id: str) -> Capability | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT data FROM capabilities WHERE capability_id = ?",
                (capability_id,),
            ).fetchone()
        if row is None:
            return None
        return Capability.model_validate_json(row[0])

    def list(self) -> list[Capability]:
        with self._connect() as conn:
            rows = conn.execute("SELECT data FROM capabilities").fetchall()
        return [Capability.model_validate_json(r[0]) for r in rows]

    def find_active_by_task_family(self, task_family: str) -> Capability | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT data FROM capabilities WHERE task_family = ? AND status = ?",
                (task_family, CapabilityStatus.ACTIVE.value),
            ).fetchone()
        if row is None:
            return None
        return Capability.model_validate_json(row[0])
