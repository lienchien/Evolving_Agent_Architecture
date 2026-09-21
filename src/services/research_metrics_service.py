from __future__ import annotations

from src.domain.research import (
    LLMInteractionMetric,
    ResearchPhase,
    TaskCostMetric,
    TokenCostSummary,
    TokenUsage,
)
from src.interfaces.repository import CapabilityRepository


_CREATION_PHASES = (
    ResearchPhase.GAP_DETECTION,
    ResearchPhase.GENERATION,
    ResearchPhase.VALIDATION,
    ResearchPhase.TESTING,
    ResearchPhase.REVISION,
    ResearchPhase.REPORT,
)
_REUSE_PHASES = (
    ResearchPhase.RETRIEVAL,
    ResearchPhase.ROUTING,
    ResearchPhase.REUSE_REASONING,
    ResearchPhase.VALIDATION,
    ResearchPhase.RESPONSE,
)


class ResearchMetricsService:
    def __init__(self, repository: CapabilityRepository) -> None:
        self._repository = repository

    def record_llm_interaction(
        self,
        *,
        task_id: str,
        task_family: str,
        capability_id: str | None,
        capability_version: str | None,
        phase: ResearchPhase,
        usage: TokenUsage,
        latency_ms: float,
        success: bool,
        error: str | None = None,
    ) -> LLMInteractionMetric:
        metric = LLMInteractionMetric(
            task_id=task_id,
            task_family=task_family,
            capability_id=capability_id,
            capability_version=capability_version,
            phase=phase,
            usage=usage,
            latency_ms=latency_ms,
            success=success,
            error=error,
        )
        self._repository.save_llm_interaction(metric)
        return metric

    @staticmethod
    def _sum_if_complete(interactions: list[LLMInteractionMetric], field: str) -> int | None:
        if not interactions:
            return 0
        values = [getattr(interaction.usage, field) for interaction in interactions]
        if any(value is None for value in values):
            return None
        return sum(values)

    @staticmethod
    def _cost_if_complete(interactions: list[LLMInteractionMetric]) -> float | None:
        if not interactions:
            return 0.0
        values = [interaction.usage.provider_cost_usd for interaction in interactions]
        if any(value is None for value in values):
            return None
        return sum(values)

    def complete_task(
        self,
        *,
        task_id: str,
        task_family: str,
        capability_id: str | None,
        capability_version: str | None,
        capability_created: bool,
        capability_reused: bool,
        latency_ms: float,
        capability_execution_ms: float | None,
        outcome_status: str,
        task_success: bool,
        error: str | None = None,
        retry_count: int = 0,
    ) -> TaskCostMetric:
        interactions = self._repository.list_llm_interactions(task_id)
        observed_creation = capability_created or any(
            item.phase == ResearchPhase.GENERATION for item in interactions
        )
        if capability_id is None:
            capability_id = next(
                (item.capability_id for item in interactions if item.capability_id is not None), None
            )
        if capability_version is None:
            capability_version = next(
                (
                    item.capability_version
                    for item in interactions
                    if item.capability_version is not None
                ),
                None,
            )
        phases = _CREATION_PHASES if observed_creation else _REUSE_PHASES
        breakdown: dict[str, int | None] = {}
        for phase in phases:
            phase_interactions = [item for item in interactions if item.phase == phase]
            breakdown[f"{phase.value}_tokens"] = self._sum_if_complete(
                phase_interactions, "total_tokens"
            )
        metric = TaskCostMetric(
            task_id=task_id,
            task_family=task_family,
            capability_id=capability_id,
            capability_version=capability_version,
            capability_created=observed_creation,
            capability_reused=capability_reused,
            input_tokens=self._sum_if_complete(interactions, "input_tokens"),
            output_tokens=self._sum_if_complete(interactions, "output_tokens"),
            reasoning_tokens=self._sum_if_complete(interactions, "reasoning_tokens"),
            total_tokens=self._sum_if_complete(interactions, "total_tokens"),
            llm_call_count=len(interactions),
            provider_cost_usd=self._cost_if_complete(interactions),
            token_breakdown=breakdown,
            latency_ms=latency_ms,
            capability_execution_ms=capability_execution_ms,
            retry_count=retry_count,
            outcome_status=outcome_status,
            task_success=task_success,
            error=error,
        )
        self._repository.save_task_cost(metric)
        return metric

    def list_tasks(
        self, task_family: str | None = None, capability_id: str | None = None,
    ) -> list[TaskCostMetric]:
        return self._repository.list_task_costs(task_family, capability_id)

    def list_interactions(self, task_id: str | None = None) -> list[LLMInteractionMetric]:
        return self._repository.list_llm_interactions(task_id)

    def summarize(
        self, task_family: str | None = None, baseline_tokens_per_task: int | None = None,
    ) -> TokenCostSummary:
        tasks = self._repository.list_task_costs(task_family=task_family)
        known = [task for task in tasks if task.total_tokens is not None]
        tokens_complete = len(known) == len(tasks) and bool(tasks)
        cumulative = sum(task.total_tokens for task in known) if tokens_complete else None
        average = cumulative / len(tasks) if cumulative is not None and tasks else None
        creation_tasks = [task for task in tasks if task.capability_created]
        reuse_tasks = [task for task in tasks if task.capability_reused]

        def average_tokens(group: list[TaskCostMetric]) -> float | None:
            if not group or any(task.total_tokens is None for task in group):
                return None
            return sum(task.total_tokens for task in group) / len(group)

        execution_times = [
            task.capability_execution_ms
            for task in tasks
            if task.capability_execution_ms is not None
        ]

        baseline_cumulative = None
        saving = None
        saving_rate = None
        break_even = None
        if baseline_tokens_per_task is not None and tasks:
            baseline_cumulative = baseline_tokens_per_task * len(tasks)
            if cumulative is not None:
                saving = baseline_cumulative - cumulative
                if baseline_cumulative:
                    saving_rate = 1 - (cumulative / baseline_cumulative)
                if task_family is not None:
                    running = 0
                    reuse_count = 0
                    for index, task in enumerate(tasks, start=1):
                        if task.total_tokens is None:
                            break
                        running += task.total_tokens
                        if task.capability_reused:
                            reuse_count += 1
                        if running < baseline_tokens_per_task * index:
                            break_even = reuse_count
                            break

        costs = [task.provider_cost_usd for task in tasks]
        cumulative_cost = None
        if tasks and all(cost is not None for cost in costs):
            cumulative_cost = sum(costs)

        note = None
        if tasks and not tokens_complete:
            note = (
                "Token totals are incomplete because at least one provider did not report usage; "
                "no token estimate or break-even value was fabricated."
            )
        elif not tasks:
            note = "No task cost metrics have been recorded."
        elif baseline_tokens_per_task is None:
            note = "Provide baseline_tokens_per_task to calculate saving and break-even metrics."
        elif task_family is None:
            note = (
                "Overall saving is shown; filter to one task_family for a meaningful "
                "break-even reuse count."
            )

        return TokenCostSummary(
            task_family=task_family,
            task_count=len(tasks),
            successful_task_count=sum(task.task_success for task in tasks),
            task_success_rate=(
                sum(task.task_success for task in tasks) / len(tasks) if tasks else None
            ),
            capability_creation_count=len(creation_tasks),
            capability_reuse_count=len(reuse_tasks),
            llm_call_count=sum(task.llm_call_count for task in tasks),
            token_data_complete=tokens_complete,
            unavailable_token_task_count=len(tasks) - len(known),
            cumulative_ceaa_tokens=cumulative,
            average_tokens_per_task=average,
            average_creation_tokens=average_tokens(creation_tasks),
            average_reuse_tokens=average_tokens(reuse_tasks),
            average_latency_ms=(
                sum(task.latency_ms for task in tasks) / len(tasks) if tasks else None
            ),
            average_capability_execution_ms=(
                sum(execution_times) / len(execution_times) if execution_times else None
            ),
            baseline_tokens_per_task=baseline_tokens_per_task,
            cumulative_baseline_tokens=baseline_cumulative,
            token_saving=saving,
            token_saving_rate=saving_rate,
            break_even_reuse_count=break_even,
            cumulative_provider_cost_usd=cumulative_cost,
            note=note,
        )
