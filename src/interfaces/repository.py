from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.capability import Capability


class CapabilityRepository(ABC):
    @abstractmethod
    def save(self, capability: Capability) -> None: ...

    @abstractmethod
    def get(self, capability_id: str) -> Capability | None: ...

    @abstractmethod
    def list(self) -> list[Capability]: ...

    @abstractmethod
    def find_active_by_task_family(self, task_family: str) -> Capability | None: ...
