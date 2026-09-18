from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import Mock

from fastapi import Depends
from fastapi.testclient import TestClient

from src.main import Container, create_app
from src.api.dependencies import get_container


def make_client(tmp_path):
    container = Container(
        database_path=str(tmp_path / "capabilities.db"),
        report_directory=str(tmp_path / "reports"),
    )
    return TestClient(create_app(container)), container


def submit_csv(client):
    return client.post(
        "/api/tasks",
        json={
            "task_family": "csv_summary",
            "description": "summarize CSV",
            "input": {"csv_text": "a,b\n1,2\n3,4\n"},
        },
    )


def test_api_full_loop_and_registry(tmp_path):
    client, container = make_client(tmp_path)

    first = submit_csv(client)
    assert first.status_code == 200
    assert first.json()["status"] == "capability_pending_approval"
    capability_id = first.json()["capability_id"]

    capability = client.get(f"/api/capabilities/{capability_id}")
    assert capability.status_code == 200
    assert capability.json()["status"] == "pending_approval"
    report = client.get(f"/api/capabilities/{capability_id}/test-report")
    assert report.status_code == 200
    assert report.json()["pass_rate"] == 1.0
    assert (tmp_path / "reports" / capability_id / "test_report.json").exists()

    assert len(client.get("/api/capabilities?status=pending_approval&task_family=csv_summary").json()) == 1
    assert client.get("/api/capabilities?status=active").json() == []
    assert client.get("/api/capabilities?offset=1&limit=1").json() == []
    assert client.get("/api/evolution/queue").json() == {"pending": 0}

    approved = client.post(f"/api/approvals/{capability_id}/approve", json={})
    assert approved.status_code == 200
    assert approved.json()["status"] == "active"
    second = submit_csv(client)
    assert second.status_code == 200
    assert second.json()["status"] == "completed"
    assert second.json()["capability_id"] == capability_id
    assert second.json()["output"]["statistics"]["a"]["sum"] == 4.0
    assert len(container.capability_service.list()) == 1
    assert len(client.get("/api/audit").json()) == 2


def test_api_approval_errors_and_validation(tmp_path):
    client, _ = make_client(tmp_path)
    assert client.get("/api/capabilities/missing").status_code == 404
    assert client.get("/api/capabilities/missing/test-report").status_code == 404
    for action in ("approve", "reject", "request-revision", "approve-with-restrictions"):
        response = client.post(f"/api/approvals/missing/{action}", json={})
        assert response.status_code == 404
        assert "unknown capability" in response.json()["detail"]

    capability_id = submit_csv(client).json()["capability_id"]
    client.post(f"/api/approvals/{capability_id}/approve", json={})
    assert client.post(f"/api/approvals/{capability_id}/approve", json={}).status_code == 409
    assert client.get("/api/capabilities?status=invalid").status_code == 422
    assert client.get("/api/capabilities?limit=0").status_code == 422
    assert client.get("/api/capabilities?offset=-1").status_code == 422


def test_api_revision_and_restrictions(tmp_path):
    client, _ = make_client(tmp_path)
    first_id = submit_csv(client).json()["capability_id"]
    revision = client.post(
        f"/api/approvals/{first_id}/request-revision",
        json={"notes": "revise"},
    )
    assert revision.status_code == 200
    assert revision.json()["status"] == "revision_requested"
    second_id = submit_csv(client).json()["capability_id"]
    assert second_id != first_id
    restricted = client.post(
        f"/api/approvals/{second_id}/approve-with-restrictions",
        json={"restrictions": {"scope": "local"}},
    )
    assert restricted.status_code == 200
    assert restricted.json()["distribution_metadata"]["restrictions"] == {"scope": "local"}


def test_default_startup_shares_container_across_first_concurrent_requests(tmp_path, monkeypatch):
    container = Container(
        database_path=str(tmp_path / "capabilities.db"),
        report_directory=str(tmp_path / "reports"),
    )
    factory = Mock(return_value=container)
    monkeypatch.setattr("src.main.Container", factory)
    app = create_app()
    factory.assert_not_called()
    assert app.state.container is None
    requests_ready = Barrier(2)

    @app.get("/test/container/{request_id}")
    def observe_container(request_id: str, current: Container = Depends(get_container)):
        requests_ready.wait(timeout=5)
        current.audit_service.record("concurrent_request", request_id)
        return {"container_id": id(current)}

    with TestClient(app) as client:
        # Startup must finish before either request can be served.
        factory.assert_called_once_with()
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(client.get, f"/test/container/{request_id}")
                for request_id in ("first", "second")
            ]
            responses = [future.result(timeout=10) for future in futures]
        assert all(response.status_code == 200 for response in responses)
        assert all(response.json()["container_id"] == id(container) for response in responses)
        audit = client.get("/api/audit")
        assert audit.status_code == 200
        assert {entry["capability_id"] for entry in audit.json()} == {"first", "second"}
        assert app.state.container is container
        factory.assert_called_once_with()


def test_startup_preserves_injected_container(tmp_path, monkeypatch):
    container = Container(
        database_path=str(tmp_path / "capabilities.db"),
        report_directory=str(tmp_path / "reports"),
    )
    container.audit_service.record("existing", "CAP-existing")
    factory = Mock(side_effect=AssertionError("Injected container must not be replaced"))
    monkeypatch.setattr("src.main.Container", factory)
    with TestClient(create_app(container)) as client:
        response = client.get("/api/audit")
        assert response.status_code == 200
        assert response.json()[0]["capability_id"] == "CAP-existing"
        assert client.app.state.container is container
    factory.assert_not_called()


def test_requests_without_startup_do_not_initialize_container(monkeypatch):
    factory = Mock(side_effect=AssertionError("Requests must not construct containers"))
    monkeypatch.setattr("src.main.Container", factory)
    app = create_app()
    # TestClient only runs lifespan when entered as a context manager.
    client = TestClient(app)
    try:
        response = client.get("/api/audit")
        assert response.status_code == 503
        assert app.state.container is None
        factory.assert_not_called()
    finally:
        client.close()
