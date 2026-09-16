from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.gap import CapabilityGap


class QueueInterface(ABC):
    @abstractmethod
    def enqueue(self, gap: CapabilityGap) -> None: ...

    @abstractmethod
    def dequeue(self) -> CapabilityGap | None: ...

    @abstractmethod
    def size(self) -> int: ...
