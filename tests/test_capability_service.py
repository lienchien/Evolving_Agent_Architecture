import pytest

from src.domain.capability import Capability, CapabilityStatus, Implementation
from src.infrastructure.sqlite_repository import SqliteCapabilityRepository
from src.services.capability_service import CapabilityService, IllegalTransitionError


def _make_service(tmp_path):
    repo = SqliteCapabilityRepository(str(tmp_path / "test.db"))
    return CapabilityService(repo)


def _make_capability() -> Capability:
    return Capability(
        name="demo",
        task_family="demo_family",
        implementation=Implementation(code="def run(input):\n    return input"),
    )


def test_valid_transition(tmp_path):
    service = _make_service(tmp_path)
    capability = _make_capability()
    service.create(capability)

    updated = service.transition(capability.capability_id, CapabilityStatus.CANDIDATE)
    assert updated.status == CapabilityStatus.CANDIDATE


def test_illegal_transition_raises(tmp_path):
    service = _make_service(tmp_path)
    capability = _make_capability()
    service.create(capability)

    with pytest.raises(IllegalTransitionError):
        service.transition(capability.capability_id, CapabilityStatus.ACTIVE)
