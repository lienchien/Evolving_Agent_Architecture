from __future__ import annotations

from fastapi import FastAPI

from src.agents.evolution_agent import EvolutionAgent
from src.agents.main_agent import MainAgent
from src.config import settings
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


class Container:
    """Manual DI container wiring the MVP's mock/in-memory adapters behind
    the interfaces defined under src/interfaces/. Swap an adapter here (e.g.
    SqliteCapabilityRepository -> a future PostgresCapabilityRepository)
    without touching services, agents, or API routes.
    """

    def __init__(self) -> None:
        repository = SqliteCapabilityRepository(settings.database_path)
        llm_provider = MockLLMProvider()
        sandbox = SubprocessSandbox()
        notification_provider = ConsoleNotificationProvider()

        self.queue = InMemoryEvolutionQueue()
        self.report_store = TestReportStore()
        self.audit_service = AuditService()

        self.capability_service = CapabilityService(repository)
        self.gap_detection_service = GapDetectionService(self.capability_service)
        self.evolution_service = EvolutionService(llm_provider, self.capability_service)
        self.validation_service = ValidationService(sandbox, self.capability_service)
        self.testing_service = TestingService(
            llm_provider, sandbox, self.capability_service, self.report_store
        )
        self.notification_service = NotificationService(notification_provider)
        self.approval_service = ApprovalService(
            self.capability_service, self.notification_service, self.audit_service
        )
        self.execution_service = CapabilityExecutionService(sandbox)

        self.evolution_agent = EvolutionAgent(
            self.evolution_service,
            self.validation_service,
            self.testing_service,
            self.approval_service,
        )
        self.main_agent = MainAgent(
            self.capability_service,
            self.gap_detection_service,
            self.execution_service,
            self.evolution_agent,
            self.queue,
        )


container = Container()

app = FastAPI(title="Capability-Evolving Agent - Phase 1 MVP")

from src.api.routes import approvals, audit, capabilities, evolution, tasks  # noqa: E402

app.include_router(tasks.router)
app.include_router(capabilities.router)
app.include_router(evolution.router)
app.include_router(approvals.router)
app.include_router(audit.router)
