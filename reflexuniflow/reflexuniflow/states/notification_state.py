import reflex as rx
from typing import TypedDict
import uuid
import datetime


class Notification(TypedDict):
    id: str
    title: str
    message: str
    kind: str
    timestamp: str
    read: bool


class NotificationState(rx.State):
    notifications: list[Notification] = []
    show_panel: bool = False

    @rx.event
    def toggle_panel(self):
        self.show_panel = not self.show_panel

    @rx.event
    def add(self, title: str, message: str, kind: str = "info"):
        self.notifications.insert(
            0,
            Notification(
                id=str(uuid.uuid4()),
                title=title,
                message=message,
                kind=kind,
                timestamp=datetime.datetime.now().strftime("%H:%M"),
                read=False,
            ),
        )
        if len(self.notifications) > 50:
            self.notifications = self.notifications[:50]

    @rx.event
    def mark_all_read(self):
        for i in range(len(self.notifications)):
            self.notifications[i]["read"] = True

    @rx.event
    def clear_all(self):
        self.notifications = []

    @rx.event
    def dismiss(self, nid: str):
        self.notifications = [n for n in self.notifications if n["id"] != nid]

    @rx.var
    def unread_count(self) -> int:
        return len([n for n in self.notifications if not n["read"]])
