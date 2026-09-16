from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventType(str, Enum):
    CAPABILITY_GAP_CREATED = "CapabilityGapCreated"
    CAPABILITY_GENERATED = "CapabilityGenerated"
    VALIDATION_STARTED = "ValidationStarted"
    VALIDATION_COMPLETED = "ValidationCompleted"
    CAPABILITY_TESTING_STARTED = "CapabilityTestingStarted"
    CAPABILITY_TESTING_COMPLETED = "CapabilityTestingCompleted"
    CAPABILITY_REPORT_GENERATED = "CapabilityReportGenerated"
    CAPABILITY_READY_FOR_REVIEW = "CapabilityReadyForReview"
    CAPABILITY_APPROVED = "CapabilityApproved"
    CAPABILITY_REJECTED = "CapabilityRejected"
    CAPABILITY_ACTIVATED = "CapabilityActivated"
    CAPABILITY_DEPRECATED = "CapabilityDeprecated"
    CAPABILITY_REVOKED = "CapabilityRevoked"


class Event(BaseModel):
    event_type: EventType
    payload: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
