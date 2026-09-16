from __future__ import annotations

from abc import ABC, abstractmethod


class NotificationProvider(ABC):
    @abstractmethod
    def send(self, subject: str, message: str) -> None: ...
