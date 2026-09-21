from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from src.domain.capability import Capability, CapabilityStatus
from src.domain.gap import CapabilityGap
from src.domain.report import TestReport
from src.services.approval_service import ApprovalService
from src.services.capability_service import CapabilityService
from src.services.evolution_service import EvolutionService
from src.services.testing_service import TestingService
from src.services.validation_service import ValidationService


class EvolutionState(TypedDict, total=False):
    task_id: str
    gap: CapabilityGap
    capability: Capability
    functional_results: list
    test_report: TestReport


class EvolutionAgent:
    def __init__(
        self,
        evolution_service: EvolutionService,
        validation_service: ValidationService,
        testing_service: TestingService,
        approval_service: ApprovalService,
        capability_service: CapabilityService,
    ) -> None:
        self._evolution_service = evolution_service
        self._validation_service = validation_service
        self._testing_service = testing_service
        self._approval_service = approval_service
        self._capability_service = capability_service
        self._graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(EvolutionState)
        graph.add_node("generate", self._generate)
        graph.add_node("validate", self._validate)
        graph.add_node("test", self._test)
        graph.add_node("finalize", self._finalize)

        graph.set_entry_point("generate")
        graph.add_edge("generate", "validate")
        graph.add_edge("validate", "test")
        graph.add_conditional_edges(
            "test",
            lambda state: (
                "finalize" if state["capability"].status == CapabilityStatus.TESTED else "end"
            ),
            {"finalize": "finalize", "end": END},
        )
        graph.add_edge("finalize", END)
        return graph.compile()

    def _generate(self, state: EvolutionState) -> dict[str, Any]:
        capability = self._evolution_service.evolve(
            state["gap"], state.get("capability"), state.get("task_id")
        )
        return {"capability": capability}

    def _validate(self, state: EvolutionState) -> dict[str, Any]:
        results = self._validation_service.validate(state["capability"])
        return {"functional_results": results}

    def _test(self, state: EvolutionState) -> dict[str, Any]:
        report = self._testing_service.run_autonomous_tests(
            state["capability"], state["functional_results"], state.get("task_id")
        )
        capability = self._capability_service.get(state["capability"].capability_id)
        return {"test_report": report, "capability": capability}

    def _finalize(self, state: EvolutionState) -> dict[str, Any]:
        capability = self._approval_service.request_approval(state["capability"])
        return {"capability": capability}

    def run(
        self, gap: CapabilityGap, reserved: Capability | None = None, task_id: str | None = None,
    ) -> EvolutionState:
        initial: EvolutionState = {"gap": gap}
        if task_id is not None:
            initial["task_id"] = task_id
        if reserved is not None:
            initial["capability"] = reserved
        return self._graph.invoke(initial)
