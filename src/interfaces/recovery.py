from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.recovery import (
    FailureAnalysis,
    RecoveryGateResult,
    RecoveryOutcome,
    RecoveryPlan,
)
from src.domain.telemetry import FailureContext


class FailureAnalysisInterface(ABC):
    @abstractmethod
    def analyze(self, context: FailureContext) -> FailureAnalysis: ...


class RecoveryPlannerInterface(ABC):
    @abstractmethod
    def plan(
        self,
        context: FailureContext,
        analysis: FailureAnalysis,
    ) -> RecoveryPlan: ...


class RecoveryGateInterface(ABC):
    @abstractmethod
    def evaluate(
        self,
        context: FailureContext,
        plan: RecoveryPlan,
    ) -> RecoveryGateResult: ...


class RecoveryOutcomeRepository(ABC):
    @abstractmethod
    def save(self, outcome: RecoveryOutcome) -> None: ...

    @abstractmethod
    def list_by_failure(self, failure_id: str) -> list[RecoveryOutcome]: ...
