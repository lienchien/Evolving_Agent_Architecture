from __future__ import annotations

from collections import deque

from src.domain.gap import CapabilityGap
from src.interfaces.queue import QueueInterface


class InMemoryEvolutionQueue(QueueInterface):
    def __init__(self) -> None:
        self._items: deque[CapabilityGap] = deque()

    def enqueue(self, gap: CapabilityGap) -> None:
        self._items.append(gap)

    def dequeue(self) -> CapabilityGap | None:
        if not self._items:
            return None
        return self._items.popleft()

    def size(self) -> int:
        return len(self._items)
