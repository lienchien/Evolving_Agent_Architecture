from __future__ import annotations

from src.interfaces.notification import NotificationProvider


class ConsoleNotificationProvider(NotificationProvider):
    def send(self, subject: str, message: str) -> None:
        print(f"[NOTIFY] {subject}: {message}")
