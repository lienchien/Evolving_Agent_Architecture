from src.domain.capability import Capability, Implementation


def test_capability_defaults():
    capability = Capability(
        name="demo",
        task_family="demo_family",
        implementation=Implementation(code="def run(input):\n    return input"),
    )
    assert capability.status.value == "draft"
    assert capability.capability_id.startswith("CAP-")
    assert capability.sharing_policy.value == "private_only"
