from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CapabilityStatus(str, Enum):
    DRAFT = "draft"
    CANDIDATE = "candidate"
    VALIDATING = "validating"
    TESTING = "testing"
    TESTED = "tested"
    FAILED = "failed"
    PENDING_APPROVAL = "pending_approval"
    REVISION_REQUESTED = "revision_requested"
    APPROVED = "approved"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    REVOKED = "revoked"
    ARCHIVED = "archived"


class SharingPolicy(str, Enum):
    PRIVATE_ONLY = "private_only"
    MANUAL_SHARE = "manual_share"
    ORGANIZATION_ONLY = "organization_only"
    GLOBAL_OPT_IN = "global_opt_in"


class CapabilityScope(str, Enum):
    PRIVATE = "private"
    LOCAL = "local"
    ORGANIZATION = "organization"
    GLOBAL = "global"


class Implementation(BaseModel):
    type: str = "python"
    code: str
    entrypoint: str = "run"


class Capability(BaseModel):
    schema_version: str = "1.0"
    capability_id: str = Field(default_factory=lambda: f"CAP-{uuid.uuid4().hex[:8]}")
    capability_version: str = "0.1.0"

    name: str
    description: str = ""

    tenant_id: str = "default"
    owner_id: str = "default"
    organization_id: str = "default"
    scope: CapabilityScope = CapabilityScope.LOCAL

    task_family: str

    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    preconditions: list[str] = Field(default_factory=list)

    dependencies: list[str] = Field(default_factory=list)
    implementation: Implementation

    validation_requirements: dict[str, Any] = Field(default_factory=dict)
    safety_requirements: dict[str, Any] = Field(default_factory=dict)

    compatibility: dict[str, Any] = Field(default_factory=dict)
    trust_level: str = "untrusted"

    status: CapabilityStatus = CapabilityStatus.DRAFT

    sharing_policy: SharingPolicy = SharingPolicy.PRIVATE_ONLY
    distribution_metadata: dict[str, Any] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
