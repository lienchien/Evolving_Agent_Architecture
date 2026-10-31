from __future__ import annotations

import uuid
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from src.agents.evolution_agent import EvolutionAgent
from src.domain.gap import CapabilityGap
from src.domain.capability import CapabilityStatus
from src.domain.errors import CapabilityConflictError, ProviderOperationError
from src.domain.telemetry import (
    DecisionEvidence,
    FailureContext,
    FailureCategory,
    FailureStage,
    ObservationKind,
    ObservationOutcome,
    RecoveryStrategy,
    RetryDecision,
    RetryDisposition,
    SideEffectStatus,
    TraceOutcome,
)
from src.interfaces.queue import QueueInterface
from src.services.capability_service import CapabilityService
from src.services.execution_service import CapabilityExecutionService
from src.services.gap_detection_service import GapDetectionService
from src.services.research_metrics_service import ResearchMetricsService
from src.interfaces.retry_policy import RetryPolicyInterface
from src.services.telemetry_service import TelemetryService


class TaskState(TypedDict, total=False):
    task_id: str
    trace_id: str
    task_family: str
    description: str
    input: dict
    capability_id: str | None
    output: dict | None
    status: str
    capability_created: bool
    capability_reused: bool
    capability_execution_ms: float
    retry_count: int
    fallback_count: int
    routing_decision_id: str


class MainAgent:
    """Owns the Task -> Capability Search -> Execute | Gap flow.

    Reserves a generation slot through the service on a search miss and hands
    its own gap to the Evolution Agent. Activation remains an approval action.
    """

    def __init__(
        self,
        capability_service: CapabilityService,
        gap_detection_service: GapDetectionService,
        execution_service: CapabilityExecutionService,
        evolution_agent: EvolutionAgent,
        queue: QueueInterface,
        research_metrics: ResearchMetricsService | None = None,
        telemetry: TelemetryService | None = None,
        retry_policy: RetryPolicyInterface | None = None,
    ) -> None:
        self._capability_service = capability_service
        self._gap_detection_service = gap_detection_service
        self._execution_service = execution_service
        self._evolution_agent = evolution_agent
        self._queue = queue
        self._research_metrics = research_metrics
        self._telemetry = telemetry
        self._retry_policy = retry_policy
        self._graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(TaskState)
        graph.add_node("search", self._search)
        graph.add_node("execute", self._execute)
        graph.add_node("evolve", self._evolve)

        graph.set_entry_point("search")
        graph.add_conditional_edges(
            "search",
            lambda state: "execute" if state.get("capability_id") else "evolve",
            {"execute": "execute", "evolve": "evolve"},
        )
        graph.add_edge("execute", END)
        graph.add_edge("evolve", END)
        return graph.compile()

    def _search(self, state: TaskState) -> dict[str, Any]:
        started_at = datetime.now(timezone.utc)
        started = perf_counter()
        try:
            candidates = self._capability_service.list_active_by_task_family(
                state["task_family"]
            )
            capability = next(
                (candidate for candidate in candidates if not candidate.fallback_eligible),
                None,
            )
        except Exception as exc:
            completed_at = datetime.now(timezone.utc)
            if self._telemetry is not None:
                observation = self._telemetry.record_observation(
                    trace_id=state["trace_id"],
                    target_type="capability_router",
                    target_id=state["task_family"],
                    target_version=None,
                    outcome=ObservationOutcome.FAILED,
                    started_at=started_at,
                    completed_at=completed_at,
                    latency_ms=(perf_counter() - started) * 1000,
                )
                self._telemetry.record_failure(
                    trace_id=state["trace_id"],
                    observation_id=observation.observation_id,
                    stage=FailureStage.ROUTING,
                    category=FailureCategory.DEPENDENCY,
                    error_code="CAPABILITY_LOOKUP_FAILED",
                    summary="Capability lookup failed",
                    exception=exc,
                    recoverable=True,
                )
            raise

        decision_id = None
        if self._telemetry is not None:
            decision = self._telemetry.record_routing_decision(
                trace_id=state["trace_id"],
                task_id=state.get("task_id"),
                candidate_ids=[item.capability_id for item in candidates],
                selected_target_id=capability.capability_id if capability else None,
                selected_target_version=(
                    capability.capability_version if capability else None
                ),
                latency_ms=(perf_counter() - started) * 1000,
                evidence=DecisionEvidence(
                    selection_criteria=["task_family_exact_match", "status_active"],
                    rationale_summary=(
                        "Selected the active capability matching the task family"
                        if capability
                        else "No active capability matched the task family"
                    ),
                    evidence_refs=[item.capability_id for item in candidates],
                    expected_outcome=(
                        "execute_active_capability"
                        if capability
                        else "evolve_capability_candidate"
                    ),
                ),
            )
            decision_id = decision.decision_id
        if capability is None:
            return {"capability_id": None, "routing_decision_id": decision_id}
        return {
            "capability_id": capability.capability_id,
            "capability_reused": True,
            "routing_decision_id": decision_id,
        }

    def _execute(self, state: TaskState) -> dict[str, Any]:
        capability_id = state.get("capability_id") or "unresolved"
        trace_id = state.get("trace_id") or f"UNPERSISTED-{state.get('task_id', 'task')}"
        capability = self._capability_service.get(capability_id)
        primary_capability = capability
        safety_requirements = (
            capability.safety_requirements if capability is not None else {}
        )
        idempotent = safety_requirements.get("idempotent")
        side_effect_status = (
            SideEffectStatus.IDEMPOTENT
            if idempotent is True
            else SideEffectStatus.NON_IDEMPOTENT
            if idempotent is False
            else SideEffectStatus.UNKNOWN
        )
        configured_max_retries = safety_requirements.get("max_retries", 0)
        max_retries = (
            configured_max_retries
            if isinstance(configured_max_retries, int)
            and not isinstance(configured_max_retries, bool)
            and configured_max_retries >= 0
            else 0
        )
        retry_count = 0
        fallback_count = 0
        attempted_capability_ids = {capability_id}
        current_decision_id = state.get("routing_decision_id")
        parent_observation_id: str | None = None
        pending_recovery: tuple[str, RetryDecision] | None = None
        pending_fallback: tuple[str, int] | None = None

        while True:
            started_at = datetime.now(timezone.utc)
            started = perf_counter()
            try:
                current_capability = self._capability_service.get(capability_id)
                if (
                    current_capability is None
                    or current_capability.status != CapabilityStatus.ACTIVE
                ):
                    raise CapabilityConflictError(
                        "Capability is no longer active; retry the task"
                    )
                if (retry_count > 0 or fallback_count > 0) and (
                    current_capability.capability_version
                    != capability.capability_version
                    or current_capability.safety_requirements.get("idempotent") is not True
                ):
                    raise CapabilityConflictError(
                        "Capability version or retry safety changed; retry the task"
                    )
                capability = current_capability
                output = self._execution_service.execute(capability, state["input"])
            except Exception as exc:
                completed_at = datetime.now(timezone.utc)
                conflict = isinstance(exc, CapabilityConflictError)
                transient = isinstance(exc, (TimeoutError, ConnectionError))
                failure_id: str | None = None
                failed_observation_id: str | None = None
                if self._telemetry is not None:
                    observation = self._telemetry.record_observation(
                        trace_id=trace_id,
                        decision_id=current_decision_id,
                        parent_observation_id=parent_observation_id,
                        kind=(
                            ObservationKind.FALLBACK
                            if fallback_count > 0
                            else ObservationKind.RETRY
                            if retry_count > 0
                            else ObservationKind.EXECUTION
                        ),
                        target_type="capability",
                        target_id=capability_id,
                        target_version=(
                            capability.capability_version if capability else None
                        ),
                        outcome=ObservationOutcome.FAILED,
                        started_at=started_at,
                        completed_at=completed_at,
                        latency_ms=(perf_counter() - started) * 1000,
                    )
                    failed_observation_id = observation.observation_id
                    if pending_recovery is not None:
                        prior_failure_id, prior_decision = pending_recovery
                        self._telemetry.record_recovery_attempt(
                            trace_id=trace_id,
                            failure_id=prior_failure_id,
                            observation_id=observation.observation_id,
                            strategy=RecoveryStrategy.RETRY,
                            target_type="capability",
                            target_id=capability_id,
                            target_version=(
                                capability.capability_version if capability else None
                            ),
                            attempt_number=retry_count,
                            outcome=ObservationOutcome.FAILED,
                            retry_decision=prior_decision,
                        )
                        pending_recovery = None
                    if pending_fallback is not None:
                        prior_failure_id, fallback_attempt = pending_fallback
                        self._telemetry.record_recovery_attempt(
                            trace_id=trace_id,
                            failure_id=prior_failure_id,
                            observation_id=observation.observation_id,
                            strategy=RecoveryStrategy.FALLBACK,
                            target_type="capability",
                            target_id=capability_id,
                            target_version=(
                                capability.capability_version if capability else None
                            ),
                            attempt_number=fallback_attempt,
                            outcome=ObservationOutcome.FAILED,
                        )
                        pending_fallback = None
                    category = (
                        FailureCategory.UNAVAILABLE
                        if conflict
                        else FailureCategory.TIMEOUT
                        if isinstance(exc, TimeoutError)
                        else FailureCategory.DEPENDENCY
                        if isinstance(exc, ConnectionError)
                        else FailureCategory.EXECUTION
                    )
                    failure = self._telemetry.record_failure(
                        trace_id=trace_id,
                        observation_id=observation.observation_id,
                        stage=(
                            FailureStage.CAPABILITY_SELECTION
                            if conflict
                            else FailureStage.TOOL_EXECUTION
                        ),
                        category=category,
                        error_code=(
                            "CAPABILITY_UNAVAILABLE"
                            if conflict
                            else "CAPABILITY_EXECUTION_TIMEOUT"
                            if isinstance(exc, TimeoutError)
                            else "CAPABILITY_DEPENDENCY_FAILED"
                            if isinstance(exc, ConnectionError)
                            else "CAPABILITY_EXECUTION_FAILED"
                        ),
                        summary=(
                            "Selected capability was unavailable"
                            if conflict
                            else "Capability execution failed"
                        ),
                        exception=exc,
                        recoverable=transient,
                    )
                    failure_id = failure.failure_id

                retry_decision = (
                    RetryDecision(
                        disposition=RetryDisposition.BLOCKED,
                        retry_allowed=False,
                        retry_count=retry_count,
                        max_retries=0,
                        side_effect_status=side_effect_status,
                        recoverable=transient,
                        reason_code="FALLBACK_TARGET_SINGLE_ATTEMPT",
                    )
                    if fallback_count > 0
                    else self._retry_policy.decide(
                        FailureContext(
                            task_id=state.get("task_id"),
                            trace_id=trace_id,
                            failure_id=failure_id or "unpersisted",
                            stage=(
                                FailureStage.CAPABILITY_SELECTION
                                if conflict
                                else FailureStage.TOOL_EXECUTION
                            ),
                            category=(
                                FailureCategory.UNAVAILABLE
                                if conflict
                                else FailureCategory.TIMEOUT
                                if isinstance(exc, TimeoutError)
                                else FailureCategory.DEPENDENCY
                                if isinstance(exc, ConnectionError)
                                else FailureCategory.EXECUTION
                            ),
                            target_type="capability",
                            target_id=capability_id,
                            target_version=(
                                capability.capability_version if capability else None
                            ),
                            exception_type=type(exc).__name__,
                            recoverable=transient,
                        ),
                        retry_count=retry_count,
                        max_retries=max_retries,
                        side_effect_status=side_effect_status,
                    )
                    if self._retry_policy is not None
                    else RetryDecision(
                        disposition=RetryDisposition.BLOCKED,
                        retry_allowed=False,
                        retry_count=retry_count,
                        max_retries=0,
                        side_effect_status=side_effect_status,
                        reason_code="RETRY_POLICY_UNAVAILABLE",
                    )
                )
                if retry_decision.retry_allowed:
                    if failure_id is not None:
                        pending_recovery = (failure_id, retry_decision)
                    parent_observation_id = failed_observation_id
                    retry_count += 1
                    continue

                fallback_candidates = (
                    self._capability_service.list_eligible_fallbacks(
                        primary_capability,
                        state["input"],
                        excluded_ids=attempted_capability_ids,
                    )
                    if primary_capability is not None
                    and side_effect_status is SideEffectStatus.IDEMPOTENT
                    and (transient or conflict)
                    else []
                )
                if fallback_candidates:
                    fallback = fallback_candidates[0]
                    if self._telemetry is not None:
                        selection_started = perf_counter()
                        decision = self._telemetry.record_routing_decision(
                            trace_id=trace_id,
                            task_id=state.get("task_id"),
                            candidate_ids=[
                                candidate.capability_id
                                for candidate in fallback_candidates
                            ],
                            selected_target_id=fallback.capability_id,
                            selected_target_version=fallback.capability_version,
                            latency_ms=(perf_counter() - selection_started) * 1000,
                            parent_decision_id=current_decision_id,
                            depth=(fallback_count + 1 if current_decision_id else 0),
                            layer="recovery",
                            node_type="alternate_capability_fallback",
                            policy_version="fallback-policy-v1",
                            fallback_reason=(
                                "selected_capability_unavailable"
                                if conflict
                                else "transient_execution_failure"
                            ),
                            evidence=DecisionEvidence(
                                selection_criteria=[
                                    "same_task_family",
                                    "active",
                                    "fallback_eligible",
                                    "identity_scope_match",
                                    "input_compatible",
                                    "idempotent",
                                    "not_previously_attempted",
                                ],
                                rationale_summary=(
                                    "Selected the highest-priority eligible alternate "
                                    "capability after a recoverable failure"
                                ),
                                evidence_refs=[
                                    fallback.capability_id,
                                    failure_id or "unpersisted_failure",
                                ],
                                expected_outcome="recover_with_alternate_capability",
                                constraints=["single_attempt_per_fallback_target"],
                            ),
                        )
                        current_decision_id = decision.decision_id

                    capability = fallback
                    capability_id = fallback.capability_id
                    attempted_capability_ids.add(capability_id)
                    safety_requirements = fallback.safety_requirements
                    side_effect_status = (
                        SideEffectStatus.IDEMPOTENT
                        if safety_requirements.get("idempotent") is True
                        else SideEffectStatus.NON_IDEMPOTENT
                        if safety_requirements.get("idempotent") is False
                        else SideEffectStatus.UNKNOWN
                    )
                    max_retries = 0
                    fallback_count += 1
                    pending_fallback = (
                        (failure_id, fallback_count)
                        if failure_id is not None
                        else None
                    )
                    parent_observation_id = failed_observation_id
                    continue

                if (
                    self._telemetry is not None
                    and failure_id is not None
                    and failed_observation_id is not None
                ):
                    now = datetime.now(timezone.utc)
                    policy_observation = self._telemetry.record_observation(
                        trace_id=trace_id,
                        decision_id=state.get("routing_decision_id"),
                        parent_observation_id=failed_observation_id,
                        kind=ObservationKind.POLICY,
                        target_type="retry_policy",
                        target_id=capability_id,
                        target_version=(
                            capability.capability_version if capability else None
                        ),
                        outcome=ObservationOutcome.CANCELLED,
                        started_at=now,
                        completed_at=now,
                        latency_ms=0,
                    )
                    self._telemetry.record_recovery_attempt(
                        trace_id=trace_id,
                        failure_id=failure_id,
                        observation_id=policy_observation.observation_id,
                        strategy=RecoveryStrategy.HUMAN_ESCALATION,
                        target_type="capability",
                        target_id=capability_id,
                        target_version=(
                            capability.capability_version if capability else None
                        ),
                        attempt_number=retry_count + fallback_count + 1,
                        outcome=ObservationOutcome.CANCELLED,
                        retry_decision=retry_decision,
                    )
                try:
                    setattr(exc, "_ceaa_retry_count", retry_count)
                    setattr(exc, "_ceaa_fallback_count", fallback_count)
                except Exception:
                    pass
                raise

            latency_ms = (perf_counter() - started) * 1000
            if self._telemetry is not None:
                observation = self._telemetry.record_observation(
                    trace_id=trace_id,
                    decision_id=current_decision_id,
                    parent_observation_id=parent_observation_id,
                    kind=(
                        ObservationKind.FALLBACK
                        if fallback_count > 0
                        else ObservationKind.RETRY
                        if retry_count > 0
                        else ObservationKind.EXECUTION
                    ),
                    target_type="capability",
                    target_id=capability.capability_id,
                    target_version=capability.capability_version,
                    outcome=ObservationOutcome.SUCCEEDED,
                    started_at=started_at,
                    completed_at=datetime.now(timezone.utc),
                    latency_ms=latency_ms,
                )
                if pending_recovery is not None:
                    prior_failure_id, prior_decision = pending_recovery
                    self._telemetry.record_recovery_attempt(
                        trace_id=trace_id,
                        failure_id=prior_failure_id,
                        observation_id=observation.observation_id,
                        strategy=RecoveryStrategy.RETRY,
                        target_type="capability",
                        target_id=capability.capability_id,
                        target_version=capability.capability_version,
                        attempt_number=retry_count,
                        outcome=ObservationOutcome.SUCCEEDED,
                        retry_decision=prior_decision,
                    )
                if pending_fallback is not None:
                    prior_failure_id, fallback_attempt = pending_fallback
                    self._telemetry.record_recovery_attempt(
                        trace_id=trace_id,
                        failure_id=prior_failure_id,
                        observation_id=observation.observation_id,
                        strategy=RecoveryStrategy.FALLBACK,
                        target_type="capability",
                        target_id=capability.capability_id,
                        target_version=capability.capability_version,
                        attempt_number=fallback_attempt,
                        outcome=ObservationOutcome.SUCCEEDED,
                    )
            return {
                "output": output,
                "status": "completed",
                "capability_id": capability.capability_id,
                "capability_reused": True,
                "capability_execution_ms": latency_ms,
                "retry_count": retry_count,
                "fallback_count": fallback_count,
            }

    def _evolve(self, state: TaskState) -> dict[str, Any]:
        started_at = datetime.now(timezone.utc)
        started = perf_counter()
        try:
            capability, owns_generation = self._capability_service.reserve_for_task(
                state["task_family"], state["description"]
            )
        except Exception as exc:
            completed_at = datetime.now(timezone.utc)
            if self._telemetry is not None:
                observation = self._telemetry.record_observation(
                    trace_id=state["trace_id"],
                    decision_id=state.get("routing_decision_id"),
                    target_type="capability_reservation",
                    target_id=state["task_family"],
                    target_version=None,
                    outcome=ObservationOutcome.FAILED,
                    started_at=started_at,
                    completed_at=completed_at,
                    latency_ms=(perf_counter() - started) * 1000,
                )
                self._telemetry.record_failure(
                    trace_id=state["trace_id"],
                    observation_id=observation.observation_id,
                    stage=FailureStage.CAPABILITY_SELECTION,
                    category=FailureCategory.DEPENDENCY,
                    error_code="CAPABILITY_RESERVATION_FAILED",
                    summary="Capability generation reservation failed",
                    exception=exc,
                    recoverable=True,
                )
            raise

        if capability.status == CapabilityStatus.ACTIVE:
            decision_id = state.get("routing_decision_id")
            if self._telemetry is not None:
                decision = self._telemetry.record_routing_decision(
                    trace_id=state["trace_id"],
                    task_id=state.get("task_id"),
                    candidate_ids=[capability.capability_id],
                    selected_target_id=capability.capability_id,
                    selected_target_version=capability.capability_version,
                    latency_ms=(perf_counter() - started) * 1000,
                    parent_decision_id=state.get("routing_decision_id"),
                    depth=1,
                    layer="reservation",
                    node_type="capability_race_resolution",
                    evidence=DecisionEvidence(
                        selection_criteria=[
                            "reservation_winner",
                            "status_active",
                        ],
                        rationale_summary=(
                            "A concurrent generation completed first; reused its "
                            "active capability"
                        ),
                        evidence_refs=[capability.capability_id],
                        expected_outcome="execute_active_capability",
                    ),
                )
                decision_id = decision.decision_id
            return self._execute(
                {
                    **state,
                    "capability_id": capability.capability_id,
                    "routing_decision_id": decision_id,
                }
            )
        if owns_generation:
            gap = CapabilityGap(
                task_family=state["task_family"], description=state["description"],
                task_input=state["input"],
            )
            # Synchronous evolution handles its own gap, never a shared dequeue.
            try:
                capability = self._evolution_agent.run(
                    gap, capability, state.get("task_id"), state.get("trace_id")
                )["capability"]
            except Exception as exc:
                provider_error = (
                    exc if isinstance(exc, ProviderOperationError) else None
                )
                root_exception = (
                    provider_error.cause if provider_error is not None else exc
                )
                current = self._capability_service.get(capability.capability_id)
                if current is not None and current.status in {
                    CapabilityStatus.DRAFT, CapabilityStatus.CANDIDATE, CapabilityStatus.VALIDATING,
                    CapabilityStatus.TESTING, CapabilityStatus.TESTED,
                }:
                    try:
                        self._capability_service.transition(current.capability_id, CapabilityStatus.FAILED)
                    except CapabilityConflictError:
                        pass  # Another state change won; do not overwrite it.
                if self._telemetry is not None:
                    observation = self._telemetry.record_observation(
                        trace_id=state["trace_id"],
                        decision_id=state.get("routing_decision_id"),
                        target_type=(
                            "llm_provider"
                            if provider_error is not None
                            else "capability_evolution"
                        ),
                        target_id=(
                            provider_error.provider_name
                            if provider_error is not None
                            else capability.capability_id
                        ),
                        target_version=(
                            None
                            if provider_error is not None
                            else capability.capability_version
                        ),
                        outcome=ObservationOutcome.FAILED,
                        started_at=started_at,
                        completed_at=datetime.now(timezone.utc),
                        latency_ms=(perf_counter() - started) * 1000,
                        metadata=(
                            {"operation": provider_error.operation}
                            if provider_error is not None
                            else {}
                        ),
                    )
                    provider_error_code = {
                        "capability_generation": (
                            "PROVIDER_CAPABILITY_GENERATION_FAILED"
                        ),
                        "boundary_test_generation": (
                            "PROVIDER_BOUNDARY_TEST_GENERATION_FAILED"
                        ),
                    }.get(
                        provider_error.operation if provider_error is not None else "",
                        "PROVIDER_OPERATION_FAILED",
                    )
                    self._telemetry.record_failure(
                        trace_id=state["trace_id"],
                        observation_id=observation.observation_id,
                        stage=(
                            FailureStage.PROVIDER
                            if provider_error is not None
                            else FailureStage.RUNTIME
                        ),
                        category=(
                            FailureCategory.TIMEOUT
                            if provider_error is not None
                            and isinstance(root_exception, TimeoutError)
                            else FailureCategory.DEPENDENCY
                            if provider_error is not None
                            else FailureCategory.EXECUTION
                        ),
                        error_code=(
                            provider_error_code
                            if provider_error is not None
                            else "CAPABILITY_EVOLUTION_FAILED"
                        ),
                        summary=(
                            "LLM provider operation failed"
                            if provider_error is not None
                            else "Capability evolution failed"
                        ),
                        exception=root_exception,
                        recoverable=(
                            isinstance(root_exception, (TimeoutError, ConnectionError))
                            if provider_error is not None
                            else True
                        ),
                    )
                raise
        evolution_failed = capability.status == CapabilityStatus.FAILED
        if self._telemetry is not None:
            observation = self._telemetry.record_observation(
                trace_id=state["trace_id"],
                decision_id=state.get("routing_decision_id"),
                target_type=(
                    "capability_evolution" if owns_generation else "capability_reservation"
                ),
                target_id=capability.capability_id,
                target_version=capability.capability_version,
                outcome=(
                    ObservationOutcome.FAILED
                    if evolution_failed
                    else ObservationOutcome.SUCCEEDED
                ),
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                latency_ms=(perf_counter() - started) * 1000,
            )
            if evolution_failed:
                self._telemetry.record_failure(
                    trace_id=state["trace_id"],
                    observation_id=observation.observation_id,
                    stage=FailureStage.VALIDATION,
                    category=FailureCategory.VALIDATION,
                    error_code="CAPABILITY_VALIDATION_FAILED",
                    summary="Generated capability did not pass validation",
                    recoverable=True,
                )
        # Followers receive the same ID and current progress without generating
        # another candidate. Submit again after activation to execute their input.
        return {
            "output": None,
            "status": f"capability_{capability.status.value}",
            "capability_id": capability.capability_id,
            "capability_created": owns_generation,
            "capability_reused": False,
        }

    def run_task(self, task_family: str, description: str, input_data: dict) -> TaskState:
        task_id = f"TASK-{uuid.uuid4().hex[:12]}"
        trace = (
            self._telemetry.start_trace(task_id=task_id, task_family=task_family)
            if self._telemetry is not None
            else None
        )
        started = perf_counter()
        try:
            result = self._graph.invoke({
                "task_id": task_id,
                **({"trace_id": trace.trace_id} if trace is not None else {}),
                "task_family": task_family,
                "description": description,
                "input": input_data,
            })
        except Exception as exc:
            if self._telemetry is not None and trace is not None:
                self._telemetry.record_unhandled_failure(
                    trace_id=trace.trace_id,
                    task_id=task_id,
                    exception=exc,
                )
            if self._research_metrics is not None:
                self._research_metrics.complete_task(
                    task_id=task_id,
                    trace_id=trace.trace_id if trace is not None else None,
                    task_family=task_family,
                    capability_id=None,
                    capability_version=None,
                    capability_created=False,
                    capability_reused=False,
                    latency_ms=(perf_counter() - started) * 1000,
                    capability_execution_ms=None,
                    outcome_status="error",
                    task_success=False,
                    error=type(exc).__name__,
                    retry_count=getattr(exc, "_ceaa_retry_count", 0),
                    fallback_count=getattr(exc, "_ceaa_fallback_count", 0),
                )
            if self._telemetry is not None and trace is not None:
                self._telemetry.complete_trace(trace.trace_id, TraceOutcome.FAILED)
            raise

        capability_id = result.get("capability_id")
        capability = self._capability_service.get(capability_id) if capability_id else None
        if self._research_metrics is not None:
            self._research_metrics.complete_task(
                task_id=task_id,
                trace_id=trace.trace_id if trace is not None else None,
                task_family=task_family,
                capability_id=capability_id,
                capability_version=capability.capability_version if capability else None,
                capability_created=result.get("capability_created", False),
                capability_reused=result.get("capability_reused", False),
                latency_ms=(perf_counter() - started) * 1000,
                capability_execution_ms=result.get("capability_execution_ms"),
                outcome_status=result.get("status", "unknown"),
                task_success=result.get("status") == "completed",
                retry_count=result.get("retry_count", 0),
                fallback_count=result.get("fallback_count", 0),
            )
        if self._telemetry is not None and trace is not None:
            status = result.get("status", "unknown")
            if status == "completed":
                outcome = TraceOutcome.SUCCEEDED
            elif status == "capability_failed":
                outcome = TraceOutcome.FAILED
            else:
                outcome = TraceOutcome.PARTIAL
            self._telemetry.complete_trace(trace.trace_id, outcome)
        result["task_id"] = task_id
        if trace is not None:
            result["trace_id"] = trace.trace_id
        return result
