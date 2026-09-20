from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from src.agents.evolution_agent import EvolutionAgent
from src.domain.gap import CapabilityGap
from src.domain.capability import CapabilityStatus
from src.domain.errors import CapabilityConflictError
from src.interfaces.queue import QueueInterface
from src.services.capability_service import CapabilityService
from src.services.execution_service import CapabilityExecutionService
from src.services.gap_detection_service import GapDetectionService


class TaskState(TypedDict, total=False):
    task_family: str
    description: str
    input: dict
    capability_id: str | None
    output: dict | None
    status: str


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
    ) -> None:
        self._capability_service = capability_service
        self._gap_detection_service = gap_detection_service
        self._execution_service = execution_service
        self._evolution_agent = evolution_agent
        self._queue = queue
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
        capability = self._capability_service.find_active_by_task_family(state["task_family"])
        if capability is None:
            return {"capability_id": None}
        return {"capability_id": capability.capability_id}

    def _execute(self, state: TaskState) -> dict[str, Any]:
        capability = self._capability_service.get(state["capability_id"])
        if capability is None or capability.status != CapabilityStatus.ACTIVE:
            raise CapabilityConflictError("Capability is no longer active; retry the task")
        output = self._execution_service.execute(capability, state["input"])
        return {"output": output, "status": "completed", "capability_id": capability.capability_id}

    def _evolve(self, state: TaskState) -> dict[str, Any]:
        capability, owns_generation = self._capability_service.reserve_for_task(
            state["task_family"], state["description"]
        )
        if capability.status == CapabilityStatus.ACTIVE:
            return self._execute({**state, "capability_id": capability.capability_id})
        if owns_generation:
            gap = CapabilityGap(
                task_family=state["task_family"], description=state["description"],
                task_input=state["input"],
            )
            # Synchronous evolution handles its own gap, never a shared dequeue.
            try:
                capability = self._evolution_agent.run(gap, capability)["capability"]
            except Exception:
                current = self._capability_service.get(capability.capability_id)
                if current is not None and current.status in {
                    CapabilityStatus.DRAFT, CapabilityStatus.CANDIDATE, CapabilityStatus.VALIDATING,
                    CapabilityStatus.TESTING, CapabilityStatus.TESTED,
                }:
                    try:
                        self._capability_service.transition(current.capability_id, CapabilityStatus.FAILED)
                    except CapabilityConflictError:
                        pass  # Another state change won; do not overwrite it.
                raise
        # Followers receive the same ID and current progress without generating
        # another candidate. Submit again after activation to execute their input.
        return {
            "output": None,
            "status": f"capability_{capability.status.value}",
            "capability_id": capability.capability_id,
        }

    def run_task(self, task_family: str, description: str, input_data: dict) -> TaskState:
        return self._graph.invoke(
            {"task_family": task_family, "description": description, "input": input_data}
        )
