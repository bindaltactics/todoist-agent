from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# Event name sets for routing in the worker/orchestrator
TASK_EVENTS = frozenset({
    "item:added",
    "item:updated",
    "item:completed",
    "item:uncompleted",
    "item:deleted",
})
COMMENT_EVENTS = frozenset({
    "note:added",
    "note:updated",
    "note:deleted",
})


class TodoistDue(BaseModel):
    date: str                   # "2025-05-20" (all-day) or "2025-05-20T11:00:00" (timed)
    timezone: str | None = None
    string: str = ""
    lang: str = "en"
    is_recurring: bool = False

    @property
    def has_time(self) -> bool:
        """True when due.date includes a time component (not an all-day date)."""
        return "T" in self.date


class TaskEventData(BaseModel):
    """Payload shape for item:* events."""
    id: str
    content: str                # task title
    description: str = ""
    project_id: str | None = None
    section_id: str | None = None
    parent_id: str | None = None
    labels: list[str] = Field(default_factory=list)
    priority: int = 1           # Todoist: 1=normal … 4=urgent
    due: TodoistDue | None = None
    added_at: datetime | None = None
    completed_at: datetime | None = None
    updated_at: datetime | None = None
    is_deleted: bool = False
    creator_id: str | None = None


class CommentEventData(BaseModel):
    """Payload shape for note:* events."""
    id: str
    task_id: str
    content: str
    posted_at: datetime
    poster_id: str
    reactions: dict[str, Any] = Field(default_factory=dict)


class TodoistInitiator(BaseModel):
    id: str
    full_name: str
    email: str | None = None
    is_premium: bool = False
    image_id: str | None = None


class TodoistWebhookEvent(BaseModel):
    event_name: str
    user_id: str
    # Kept as raw dict so the worker can validate into the correct typed submodel
    event_data: dict[str, Any]
    initiator: TodoistInitiator
    version: str = "8"

    @property
    def is_task_event(self) -> bool:
        return self.event_name in TASK_EVENTS

    @property
    def is_comment_event(self) -> bool:
        return self.event_name in COMMENT_EVENTS

    def task_data(self) -> TaskEventData:
        return TaskEventData.model_validate(self.event_data)

    def comment_data(self) -> CommentEventData:
        return CommentEventData.model_validate(self.event_data)
