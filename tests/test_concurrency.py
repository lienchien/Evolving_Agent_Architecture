from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Lock
import json
import sqlite3
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from src.main import Container, create_app
from src.domain.capability import Capability, CapabilityStatus, Implementation
from src.domain.errors import CapabilityConflictError
from src.infrastructure.sqlite_repository import SqliteCapabilityRepository


def make_container(tmp_path):
    return Container(str(tmp_path / "shared.db"), str(tmp_path / "reports"))


def pending_capability(container, family="decision"):
    capability = Capability(
        name=family, task_family=family, status=CapabilityStatus.PENDING_APPROVAL,
        implementation=Implementation(code="def run(input): return input"),
    )
    return container.capability_service.create(capability)


def test_competing_decisions_only_one_commits(tmp_path, monkeypatch):
    container = make_container(tmp_path)
    capability = pending_capability(container)
    repo = container.capability_service._repository
    original_get = repo.get
    both_read = Barrier(2)

    def synchronized_get(capability_id):
        value = original_get(capability_id)
        if value.status == CapabilityStatus.PENDING_APPROVAL:
            both_read.wait(timeout=10)
        return value

    monkeypatch.setattr(repo, "get", synchronized_get)
    with TestClient(create_app(container)) as client:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(client.post,
                f"/api/approvals/{capability.capability_id}/{action}", json={})
                for action in ("approve", "reject")]
            responses = [future.result(timeout=15) for future in futures]
    assert sorted(response.status_code for response in responses) == [200, 409]
    winning = next(response.json() for response in responses if response.status_code == 200)
    assert original_get(capability.capability_id).status.value == winning["status"]
    assert len(container.approval_service.list_records()) == 1
    assert len(container.audit_service.list()) == 1


def test_stale_update_cannot_overwrite_newer_state(tmp_path):
    container = make_container(tmp_path)
    capability = pending_capability(container)
    stale = container.capability_service.get(capability.capability_id)
    container.approval_service.reject(capability.capability_id)
    stale.description = "stale metadata"
    with pytest.raises(CapabilityConflictError):
        container.capability_service.update(stale)
    current = container.capability_service.get(capability.capability_id)
    assert current.status == CapabilityStatus.ARCHIVED
    assert current.description != "stale metadata"


def test_concurrent_different_tasks_keep_their_own_capabilities(tmp_path, monkeypatch):
    container = make_container(tmp_path)
    original_run = container.evolution_agent.run
    both_generating = Barrier(2)

    def synchronized_run(gap, *args, **kwargs):
        both_generating.wait(timeout=10)
        return original_run(gap, *args, **kwargs)

    def unexpected_queue_use(*args):
        pytest.fail("Synchronous evolution must not use a shared work queue")

    monkeypatch.setattr(container.evolution_agent, "run", synchronized_run)
    monkeypatch.setattr(container.queue, "enqueue", unexpected_queue_use)
    monkeypatch.setattr(container.queue, "dequeue", unexpected_queue_use)
    with TestClient(create_app(container)) as client:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = {family: pool.submit(client.post, "/api/tasks", json={
                "task_family": family, "input": {"csv_text": "a\n1\n", "text": "one two"}
            }) for family in ("csv_task", "word_task")}
            for family, future in futures.items():
                response = future.result(timeout=15)
                assert response.status_code == 200
                capability = container.capability_service.get(response.json()["capability_id"])
                assert capability.task_family == family


def test_24_same_family_requests_share_one_generation_across_apps(tmp_path, monkeypatch):
    containers = [make_container(tmp_path), make_container(tmp_path)]
    generation_calls = []
    lock = Lock()
    for container in containers:
        provider = container.evolution_service._llm_provider
        original = provider.generate_capability

        def counted(gap, generate=original):
            with lock:
                generation_calls.append(gap.gap_id)
            return generate(gap)

        monkeypatch.setattr(provider, "generate_capability", counted)

    start = Barrier(24)
    with TestClient(create_app(containers[0])) as a, TestClient(create_app(containers[1])) as b:
        clients = [a, b]

        def submit(index):
            start.wait(timeout=15)
            return clients[index % 2].post("/api/tasks", json={"task_family": "burst_words"})

        with ThreadPoolExecutor(max_workers=24) as pool:
            responses = list(pool.map(submit, range(24)))
        assert all(response.status_code == 200 for response in responses)
        capability_ids = {response.json()["capability_id"] for response in responses}
        assert len(capability_ids) == 1
        assert len(generation_calls) == 1
        capability_id = capability_ids.pop()
        assert len(containers[0].capability_service.list()) == 1

        def approve(index):
            return clients[index % 2].post(f"/api/approvals/{capability_id}/approve", json={})

        with ThreadPoolExecutor(max_workers=24) as pool:
            approvals = list(pool.map(approve, range(24)))
        assert [r.status_code for r in approvals].count(200) == 1
        assert [r.status_code for r in approvals].count(409) == 23
        assert containers[0].capability_service.get(capability_id).status == CapabilityStatus.ACTIVE
        assert len(containers[0].approval_service.list_records()) == 1
        assert containers[0].audit_service.list() == containers[1].audit_service.list()


def test_database_rejects_duplicate_active_family(tmp_path):
    container = make_container(tmp_path)
    first = pending_capability(container, "unique_family")
    container.approval_service.approve(first.capability_id)
    duplicate = Capability(
        name="duplicate", task_family="unique_family", status=CapabilityStatus.ACTIVE,
        implementation=Implementation(code="def run(input): return input"),
    )
    with pytest.raises(CapabilityConflictError):
        container.capability_service.create(duplicate)
    assert len(container.capability_service.list()) == 1


def test_generation_exception_releases_family_for_retry(tmp_path, monkeypatch):
    container = make_container(tmp_path)
    provider = container.evolution_service._llm_provider
    original = provider.generate_capability

    def unavailable(gap):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(provider, "generate_capability", unavailable)
    with TestClient(create_app(container), raise_server_exceptions=False) as client:
        first = client.post("/api/tasks", json={"task_family": "retry_words"})
        assert first.status_code == 500
        failed = container.capability_service.list()[0]
        assert failed.status == CapabilityStatus.FAILED
        monkeypatch.setattr(provider, "generate_capability", original)
        second = client.post("/api/tasks", json={"task_family": "retry_words"})
        assert second.status_code == 200
        assert second.json()["status"] == "capability_pending_approval"
        assert second.json()["capability_id"] != failed.capability_id


def test_decision_and_audit_roll_back_together(tmp_path, monkeypatch):
    container = make_container(tmp_path)
    capability = pending_capability(container)
    repo = container.capability_service._repository
    original = repo._insert_audit

    def unavailable(conn, entry):
        raise RuntimeError("audit storage unavailable")

    monkeypatch.setattr(repo, "_insert_audit", unavailable)
    with pytest.raises(RuntimeError, match="audit storage unavailable"):
        container.approval_service.approve_with_restrictions(capability.capability_id, {"scope": "local"})
    unchanged = repo.get(capability.capability_id)
    assert unchanged.status == CapabilityStatus.PENDING_APPROVAL
    assert unchanged.revision == capability.revision
    assert "restrictions" not in unchanged.distribution_metadata
    assert container.approval_service.list_records() == []
    assert container.audit_service.list() == []
    monkeypatch.setattr(repo, "_insert_audit", original)
    container.approval_service.approve(capability.capability_id)
    assert len(container.approval_service.list_records()) == 1


def test_reports_and_governance_survive_other_apps_and_restart(tmp_path):
    first = make_container(tmp_path)
    other = Container(str(tmp_path / "shared.db"), str(tmp_path / "other-reports"))
    with TestClient(create_app(first)) as a, TestClient(create_app(other)) as b:
        created = a.post("/api/tasks", json={"task_family": "persistent_words"}).json()
        capability_id = created["capability_id"]
        report_url = f"/api/capabilities/{capability_id}/test-report"
        assert b.get(report_url).status_code == 200
        assert a.get(report_url).json() == b.get(report_url).json()
        assert not (tmp_path / "other-reports").exists()
        assert a.get("/api/audit").json() == b.get("/api/audit").json()
        assert b.post(f"/api/approvals/{capability_id}/approve-with-restrictions", json={
            "reviewer": "developer", "restrictions": {"reviewer": "untrusted-metadata", "scope": "local"}
        }).status_code == 200
        assert first.approval_service.list_records() == other.approval_service.list_records()
        record = first.approval_service.list_records()[0]
        assert record.reviewer == "developer"
        assert record.restrictions["scope"] == "local"
        assert first.audit_service.list()[-1]["metadata"]["reviewer"] == "developer"

    restarted = make_container(tmp_path)
    assert restarted.report_store.get(capability_id) == first.report_store.get(capability_id)
    assert restarted.approval_service.list_records() == first.approval_service.list_records()
    assert restarted.audit_service.list() == first.audit_service.list()

    # A fresh OS process verifies these results do not come from shared memory.
    code = """
import json, sys
from src.main import Container
c = Container(sys.argv[1], sys.argv[2])
print(json.dumps({"report": c.report_store.get(sys.argv[3]).capability_id,
                  "approvals": len(c.approval_service.list_records()),
                  "audit": len(c.audit_service.list())}))
"""
    child = subprocess.run(
        [sys.executable, "-B", "-c", code, str(tmp_path / "shared.db"),
         str(tmp_path / "child-reports"), capability_id],
        capture_output=True, text=True, timeout=30, check=True,
    )
    assert json.loads(child.stdout) == {"report": capability_id, "approvals": 1, "audit": 2}


def test_reservation_is_unique_across_processes(tmp_path):
    code = """
import json, sys
from src.infrastructure.sqlite_repository import SqliteCapabilityRepository
r = SqliteCapabilityRepository(sys.argv[1])
c, owned = r.reserve_for_task("same_family", "concurrent processes")
print(json.dumps({"id": c.capability_id, "owned": owned}))
"""
    def run_child(_):
        child = subprocess.run(
            [sys.executable, "-B", "-c", code, str(tmp_path / "processes.db")],
            capture_output=True, text=True, timeout=30, check=True,
        )
        return json.loads(child.stdout)

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(run_child, range(4)))
    assert len({result["id"] for result in results}) == 1
    assert sum(result["owned"] for result in results) == 1


def test_only_one_process_can_approve_and_persist_success(tmp_path):
    container = make_container(tmp_path)
    capability = pending_capability(container)
    capability.capability_version = "2.0.0"
    container.capability_service.update(capability)
    code = """
import json, sys
from src.main import Container
from src.domain.errors import CapabilityConflictError
c = Container(sys.argv[1], sys.argv[2])
try:
    c.approval_service.approve(sys.argv[3])
    print(json.dumps({"status": 200}))
except CapabilityConflictError:
    print(json.dumps({"status": 409}))
"""
    def run_child(_):
        child = subprocess.run(
            [sys.executable, "-B", "-c", code, str(tmp_path / "shared.db"),
             str(tmp_path / "reports"), capability.capability_id],
            capture_output=True, text=True, timeout=30, check=True,
        )
        return json.loads(child.stdout)["status"]

    with ThreadPoolExecutor(max_workers=4) as pool:
        statuses = list(pool.map(run_child, range(4)))
    assert sorted(statuses) == [200, 409, 409, 409]
    assert container.capability_service.get(capability.capability_id).status == CapabilityStatus.ACTIVE
    records = container.approval_service.list_records()
    assert len(records) == 1
    assert records[0].capability_version == "2.0.0"
    assert len(container.audit_service.list()) == 1


def test_activation_between_search_and_reservation_keeps_response_id(tmp_path, monkeypatch):
    container = make_container(tmp_path)
    with TestClient(create_app(container)) as client:
        capability_id = client.post("/api/tasks", json={"task_family": "words"}).json()["capability_id"]
        client.post(f"/api/approvals/{capability_id}/approve", json={})
        # Simulate an earlier search missing the now-active capability.
        monkeypatch.setattr(container.capability_service, "find_active_by_task_family", lambda _: None)
        response = client.post("/api/tasks", json={"task_family": "words", "input": {"text": "one two"}})
        assert response.status_code == 200
        assert response.json()["status"] == "completed"
        assert response.json()["capability_id"] == capability_id
        assert response.json()["output"]["word_count"] == 2


def make_legacy_database(path, capabilities):
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE capabilities (capability_id TEXT PRIMARY KEY, task_family TEXT NOT NULL, status TEXT NOT NULL, data TEXT NOT NULL)")
        for capability in capabilities:
            conn.execute("INSERT INTO capabilities VALUES (?, ?, ?, ?)", (
                capability.capability_id, capability.task_family, capability.status.value,
                capability.model_dump_json(exclude={"revision"}),
            ))
        conn.commit()
    finally:
        conn.close()


def test_legacy_schema_migration_preserves_data(tmp_path):
    capability = Capability(name="legacy", task_family="legacy", implementation=Implementation(code=""))
    path = tmp_path / "legacy.db"
    make_legacy_database(path, [capability])
    repo = SqliteCapabilityRepository(str(path))
    restored = repo.get(capability.capability_id)
    assert restored.revision == 0
    restored.description = "updated"
    repo.save(restored)
    assert repo.get(capability.capability_id).revision == 1


def test_legacy_duplicates_require_explicit_resolution(tmp_path):
    capabilities = [Capability(name="legacy", task_family="same", status=CapabilityStatus.ACTIVE,
        implementation=Implementation(code="")) for _ in range(2)]
    path = tmp_path / "legacy-duplicates.db"
    make_legacy_database(path, capabilities)
    with pytest.raises(CapabilityConflictError, match="multiple open capabilities"):
        SqliteCapabilityRepository(str(path))
    conn = sqlite3.connect(path)
    try:
        assert conn.execute("SELECT count(*) FROM capabilities").fetchone()[0] == 2
    finally:
        conn.close()
