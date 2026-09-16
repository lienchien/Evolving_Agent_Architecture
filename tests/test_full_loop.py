from tests.support import build_main_agent


def test_full_capability_lifecycle(tmp_path):
    main_agent, capability_service, approval_service = build_main_agent(tmp_path)

    first = main_agent.run_task(
        task_family="csv_summary",
        description="summarize numeric columns of a csv file",
        input_data={"csv_text": "a,b\n1,2\n3,4\n"},
    )
    assert first["status"] == "capability_pending_approval"
    capability_id = first["capability_id"]

    capabilities = capability_service.list()
    assert len(capabilities) == 1
    assert capabilities[0].status.value == "pending_approval"

    approval_service.approve(capability_id)
    assert capability_service.get(capability_id).status.value == "active"

    second = main_agent.run_task(
        task_family="csv_summary",
        description="summarize numeric columns of a csv file",
        input_data={"csv_text": "a,b\n1,2\n3,4\n"},
    )
    assert second["status"] == "completed"
    assert second["capability_id"] == capability_id
    assert second["output"]["statistics"]["a"]["sum"] == 4.0

    assert len(capability_service.list()) == 1
