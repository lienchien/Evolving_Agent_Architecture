from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from src.agents.evolution_agent import EvolutionAgent
from src.domain.gap import CapabilityGap
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

    Per design doc Section 5, the Main Agent may not modify, activate, or
    publish capabilities directly -- it only searches, executes, and (on a
    miss) hands a CapabilityGap to the Evolution Agent.
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
        output = self._execution_service.execute(capability, state["input"])
        return {"output": output, "status": "completed"}

    def _evolve(self, state: TaskState) -> dict[str, Any]:
        gap: CapabilityGap | None = self._gap_detection_service.detect(
            state["task_family"], state["description"], state["input"]
        )
        if gap is None:
            return self._execute(state)

        self._queue.enqueue(gap)
        queued_gap = self._queue.dequeue()
        assert queued_gap is not None

        result = self._evolution_agent.run(queued_gap)
        capability = result["capability"]
        return {
            "output": None,
            "status": f"capability_{capability.status.value}",
            "capability_id": capability.capability_id,
        }

    def run_task(self, task_family: str, description: str, input_data: dict) -> TaskState:
        return self._graph.invoke(
            {"task_family": task_family, "description": description, "input": input_data}
        )
