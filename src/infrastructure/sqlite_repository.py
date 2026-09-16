from __future__ import annotations

import sqlite3
from pathlib import Path

from src.domain.capability import Capability, CapabilityStatus
from src.interfaces.repository import CapabilityRepository


class SqliteCapabilityRepository(CapabilityRepository):
    def __init__(self, db_path: str = "capability_library.db") -> None:
        self._db_path = db_path
        parent = Path(db_path).parent
        if str(parent) not in ("", "."):
            parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS capabilities (
                    capability_id TEXT PRIMARY KEY,
                    task_family TEXT NOT NULL,
                    status TEXT NOT NULL,
                    data TEXT NOT NULL
                )
                """
            )

    def save(self, capability: Capability) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO capabilities (capability_id, task_family, status, data)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(capability_id) DO UPDATE SET
                    task_family = excluded.task_family,
                    status = excluded.status,
                    data = excluded.data
                """,
                (
                    capability.capability_id,
                    capability.task_family,
                    capability.status.value,
                    capability.model_dump_json(),
                ),
            )

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
