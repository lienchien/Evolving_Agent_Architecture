from src.agents.evolution_agent import EvolutionAgent
from src.agents.main_agent import MainAgent
from src.infrastructure.console_notification import ConsoleNotificationProvider
from src.infrastructure.memory_queue import InMemoryEvolutionQueue
from src.infrastructure.mock_llm import MockLLMProvider
from src.infrastructure.sqlite_repository import SqliteCapabilityRepository
from src.infrastructure.subprocess_sandbox import SubprocessSandbox
from src.services.approval_service import ApprovalService
from src.services.audit_service import AuditService
from src.services.capability_service import CapabilityService
from src.services.evolution_service import EvolutionService
from src.services.execution_service import CapabilityExecutionService
from src.services.gap_detection_service import GapDetectionService
from src.services.notification_service import NotificationService
from src.services.report_store import TestReportStore
from src.services.testing_service import TestingService
from src.services.validation_service import ValidationService


def _build_main_agent(tmp_path):
    repository = SqliteCapabilityRepository(str(tmp_path / "capabilities.db"))
    llm_provider = MockLLMProvider()
    sandbox = SubprocessSandbox()

    capability_service = CapabilityService(repository)
    gap_detection_service = GapDetectionService(capability_service)
    evolution_service = EvolutionService(llm_provider, capability_service)
    validation_service = ValidationService(sandbox, capability_service)
    report_store = TestReportStore()
    testing_service = TestingService(llm_provider, sandbox, capability_service, report_store)
    notification_service = NotificationService(ConsoleNotificationProvider())
    audit_service = AuditService()
    approval_service = ApprovalService(capability_service, notification_service, audit_service)
    execution_service = CapabilityExecutionService(sandbox)
    queue = InMemoryEvolutionQueue()

    evolution_agent = EvolutionAgent(
        evolution_service, validation_service, testing_service, approval_service
    )
    main_agent = MainAgent(
        capability_service, gap_detection_service, execution_service, evolution_agent, queue
    )
    return main_agent, capability_service, approval_service


def test_full_capability_lifecycle(tmp_path):
    main_agent, capability_service, approval_service = _build_main_agent(tmp_path)

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
