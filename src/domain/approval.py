from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class ApprovalDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"
    APPROVED_WITH_RESTRICTIONS = "approved_with_restrictions"


class ApprovalRecord(BaseModel):
    approval_id: str = Field(default_factory=lambda: f"APR-{uuid.uuid4().hex[:8]}")
    capability_id: str
    capability_version: str
    decision: ApprovalDecision
    reviewer: str = "administrator"
    notes: str = ""
    restrictions: dict = Field(default_factory=dict)
    decided_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
