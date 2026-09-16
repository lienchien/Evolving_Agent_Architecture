from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class GapType(str, Enum):
    MISSING_CAPABILITY = "missing_capability"
    INSUFFICIENT_CAPABILITY = "insufficient_capability"
    INTEGRATION_GAP = "integration_gap"
    RELIABILITY_GAP = "reliability_gap"
    EFFICIENCY_GAP = "efficiency_gap"
    SAFETY_GAP = "safety_gap"


class CapabilityGap(BaseModel):
    gap_id: str = Field(default_factory=lambda: f"GAP-{uuid.uuid4().hex[:8]}")
    task_family: str
    description: str
    gap_type: GapType = GapType.MISSING_CAPABILITY
    task_input: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
