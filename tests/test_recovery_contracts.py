from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.domain.recovery import (
    FailureAnalysis,
    RecoveryGateResult,
    RecoveryGateStatus,
    RecoveryOutcome,
    RecoveryPlan,
    RecoveryResolution,
)
from src.domain.telemetry import FailureCategory, FailureContext, FailureStage
from src.interfaces.recovery import (
    FailureAnalysisInterface,
    RecoveryGateInterface,
    RecoveryOutcomeRepository,
    RecoveryPlannerInterface,
)


class _MockFailureAnalysis(FailureAnalysisInterface):
    def analyze(self, context: FailureContext) -> FailureAnalysis:
        return FailureAnalysis(
            trace_id=context.trace_id,
            failure_id=context.failure_id,
            diagnosis_summary="Transient provider timeout hypothesis",
            evidence_refs=[context.failure_id],
            analyzer="mock-diagnostics",
            analyzer_version="1",
        )


class _MockRecoveryPlanner(RecoveryPlannerInterface):
    def plan(
        self,
        context: FailureContext,
        analysis: FailureAnalysis,
    ) -> RecoveryPlan:
        return RecoveryPlan(
            trace_id=context.trace_id,
            failure_id=context.failure_id,
            analysis_id=analysis.analysis_id,
            candidate_action="Request human review of provider health",
            scope=["provider-health"],
            risk_level="low",
            evidence_requirements=["fresh health check"],
            rollback_plan="No mutation was performed",
            max_repair_cycles=0,
        )


class _MockRecoveryGate(RecoveryGateInterface):
    def __init__(self, status: RecoveryGateStatus) -> None:
        self._status = status

    def evaluate(
        self,
        context: FailureContext,
        plan: RecoveryPlan,
    ) -> RecoveryGateResult:
        return RecoveryGateResult(
            status=self._status,
            resume_allowed=self._status is RecoveryGateStatus.APPROVED,
            reason_codes=[f"MOCK_{self._status.value.upper()}"],
            policy_version="test-policy-1",
        )


class _MockRecoveryOutcomeRepository(RecoveryOutcomeRepository):
    def __init__(self) -> None:
        self._items: list[RecoveryOutcome] = []

    def save(self, outcome: RecoveryOutcome) -> None:
        self._items.append(outcome)

    def list_by_failure(self, failure_id: str) -> list[RecoveryOutcome]:
        return [item for item in self._items if item.failure_id == failure_id]


def _context() -> FailureContext:
    return FailureContext(
        task_id="TASK-recovery",
        trace_id="TRACE-recovery",
        span_id="OBS-recovery",
        failure_id="FAIL-recovery",
        stage=FailureStage.PROVIDER,
        category=FailureCategory.TIMEOUT,
        target_type="provider",
        target_id="mock-provider",
        exception_type="TimeoutError",
        recoverable=True,
        checkpoint_ref="CHECKPOINT-before-provider-call",
    )


@pytest.mark.parametrize(
    "status",
    [RecoveryGateStatus.DENIED, RecoveryGateStatus.UNKNOWN],
)
def test_denied_and_unknown_recovery_gates_fail_closed(status):
    context = _context()
    analysis = _MockFailureAnalysis().analyze(context)
    plan = _MockRecoveryPlanner().plan(context, analysis)
    gate = _MockRecoveryGate(status).evaluate(context, plan)

    assert gate.resume_allowed is False
    outcome = RecoveryOutcome(
        trace_id=context.trace_id,
        failure_id=context.failure_id,
        recovery_plan_id=plan.recovery_plan_id,
        gate_status=gate.status,
        diagnosis_summary=analysis.diagnosis_summary,
        validation_result="Not executed because the gate did not approve",
        resolution=RecoveryResolution.ESCALATED,
    )
    repository = _MockRecoveryOutcomeRepository()
    repository.save(outcome)
    assert repository.list_by_failure(context.failure_id) == [outcome]


def test_recovery_contract_rejects_unsafe_gate_and_false_resolution():
    with pytest.raises(ValidationError, match="must fail closed"):
        RecoveryGateResult(
            status=RecoveryGateStatus.UNKNOWN,
            resume_allowed=True,
        )

    with pytest.raises(ValidationError, match="cannot record a resolved recovery"):
        RecoveryOutcome(
            trace_id="TRACE-invalid",
            failure_id="FAIL-invalid",
            gate_status=RecoveryGateStatus.DENIED,
            resolution=RecoveryResolution.RESOLVED,
        )

    with pytest.raises(ValidationError, match="independent validation evidence"):
        RecoveryOutcome(
            trace_id="TRACE-unvalidated",
            failure_id="FAIL-unvalidated",
            gate_status=RecoveryGateStatus.APPROVED,
            resolution=RecoveryResolution.RESOLVED,
        )
