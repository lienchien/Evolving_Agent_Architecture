from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.domain.errors import CapabilityConflictError

from src.agents.evolution_agent import EvolutionAgent
from src.agents.main_agent import MainAgent
from src.config import settings
from src.infrastructure.console_notification import ConsoleNotificationProvider
from src.infrastructure.memory_queue import InMemoryEvolutionQueue
from src.infrastructure.mock_llm import MockLLMProvider
from src.infrastructure.sqlite_repository import SqliteCapabilityRepository
from src.infrastructure.subprocess_sandbox import SubprocessSandbox
from src.interfaces.llm import LLMProvider
from src.services.approval_service import ApprovalService
from src.services.audit_service import AuditService
from src.services.capability_service import CapabilityService
from src.services.evolution_service import EvolutionService
from src.services.execution_service import CapabilityExecutionService
from src.services.gap_detection_service import GapDetectionService
from src.services.notification_service import NotificationService
from src.services.report_store import TestReportStore
from src.services.research_metrics_service import ResearchMetricsService
from src.services.testing_service import TestingService
from src.services.validation_service import ValidationService


class Container:
    """Manual DI container wiring the MVP's mock/in-memory adapters behind
    the interfaces defined under src/interfaces/. Swap an adapter here (e.g.
    SqliteCapabilityRepository -> a future PostgresCapabilityRepository)
    without touching services, agents, or API routes.
    """

    def __init__(
        self,
        database_path: str | None = None,
        report_directory: str = "capability_library",
        llm_provider: LLMProvider | None = None,
    ) -> None:
        repository = SqliteCapabilityRepository(
            database_path if database_path is not None else settings.database_path
        )
        llm_provider = llm_provider or MockLLMProvider()
        sandbox = SubprocessSandbox()
        notification_provider = ConsoleNotificationProvider()

        self.queue = InMemoryEvolutionQueue()
        self.report_store = TestReportStore(repository)
        self.audit_service = AuditService(repository)
        self.research_metrics_service = ResearchMetricsService(repository)

        self.capability_service = CapabilityService(repository)
        self.gap_detection_service = GapDetectionService(self.capability_service)
        self.evolution_service = EvolutionService(
            llm_provider, self.capability_service, self.research_metrics_service
        )
        self.validation_service = ValidationService(sandbox, self.capability_service)
        self.testing_service = TestingService(
            llm_provider,
            sandbox,
            self.capability_service,
            self.report_store,
            report_directory,
            self.research_metrics_service,
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
            self.capability_service,
        )
        self.main_agent = MainAgent(
            self.capability_service,
            self.gap_detection_service,
            self.execution_service,
            self.evolution_agent,
            self.queue,
            self.research_metrics_service,
        )


from src.api.routes import approvals, audit, capabilities, evolution, research, tasks  # noqa: E402


def create_app(container: Container | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Initialize before serving requests so concurrent requests cannot replace
        # the shared service graph. Each worker owns a container, while workers
        # using the same database share capabilities, reports and governance data.
        if app.state.container is None:
            app.state.container = Container()
        yield

    app = FastAPI(title="Capability-Evolving Agent - Phase 1 MVP", lifespan=lifespan)
    app.state.container = container

    @app.exception_handler(CapabilityConflictError)
    async def capability_conflict(request: Request, exc: CapabilityConflictError):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    app.include_router(tasks.router)
    app.include_router(capabilities.router)
    app.include_router(evolution.router)
    app.include_router(approvals.router)
    app.include_router(audit.router)
    app.include_router(research.router)
    return app


app = create_app()
