from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class AuditService:
    def __init__(self) -> None:
        self._entries: list[dict[str, Any]] = []

    def record(self, action: str, capability_id: str, metadata: dict[str, Any] | None = None) -> None:
        self._entries.append(
            {
                "action": action,
                "capability_id": capability_id,
                "metadata": metadata or {},
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    def list(self) -> list[dict[str, Any]]:
        return list(self._entries)
