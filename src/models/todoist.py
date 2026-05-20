from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

# ── Event routing sets ────────────────────────────────────────────────────────

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
PROJECT_EVENTS = frozenset({
    "project:added",
    "project:updated",
    "project:deleted",
    "project:archived",
    "project:unarchived",
})
LABEL_EVENTS = frozenset({"label:added", "label:updated", "label:deleted"})
FILTER_EVENTS = frozenset({"filter:added", "filter:updated", "filter:deleted"})
REMINDER_EVENTS = frozenset({"reminder:fired"})

ALL_EVENTS = (
    TASK_EVENTS | COMMENT_EVENTS | PROJECT_EVENTS
    | LABEL_EVENTS | FILTER_EVENTS | REMINDER_EVENTS
)

# ── Shared sub-objects ────────────────────────────────────────────────────────


class TodoistDue(BaseModel):
    # date is either "YYYY-MM-DD" (all-day) or "YYYY-MM-DDTHH:MM:SS" (timed,
    # floating or fixed-timezone). Check has_time before assuming a clock time.
    date: str
    string: str = ""
    lang: str = "en"
    is_recurring: bool = False
    timezone: str | None = None  # set only for fixed-timezone due times

    @property
    def has_time(self) -> bool:
        """True when the due date includes a clock time (not an all-day entry)."""
        return "T" in self.date


class TodoistDeadline(BaseModel):
    """Hard deadline added in API v1 — separate from the due date."""
    date: str   # "YYYY-MM-DD"
    lang: str = "en"


class TodoistDuration(BaseModel):
    amount: int
    unit: Literal["minute", "day"]


class TodoistAttachment(BaseModel):
    resource_type: str | None = None
    file_name: str | None = None
    file_size: int | None = None
    file_type: str | None = None
    file_url: str | None = None
    image: str | None = None
    image_width: int | None = None
    image_height: int | None = None
    url: str | None = None
    title: str | None = None


# ── Event data models ─────────────────────────────────────────────────────────


class TaskEventData(BaseModel):
    """
    Payload shape for item:* events.

    Field names follow the Sync API / webhook convention (e.g. added_at, not
    created_at). Once Todoist completes the API v1 webhook revamp these may
    change — at that point align with the REST API v1 model (created_at, etc.).
    Priority: 1=normal, 2=medium, 3=high, 4=urgent.
    """
    id: str
    content: str                        # task title
    description: str = ""
    project_id: str | None = None
    section_id: str | None = None
    parent_id: str | None = None
    labels: list[str] = Field(default_factory=list)
    priority: int = 1
    due: TodoistDue | None = None
    deadline: TodoistDeadline | None = None
    duration: TodoistDuration | None = None
    is_collapsed: bool = False
    order: int = 0
    assignee_id: str | None = None
    assigner_id: str | None = None
    creator_id: str | None = None
    added_at: datetime | None = None    # creation timestamp in webhook payloads
    completed_at: datetime | None = None
    updated_at: datetime | None = None
    is_deleted: bool = False


class CommentEventData(BaseModel):
    """Payload shape for note:* events."""
    id: str
    task_id: str
    content: str
    posted_at: datetime
    poster_id: str
    attachment: TodoistAttachment | None = None


class TodoistInitiator(BaseModel):
    id: str
    full_name: str
    email: str | None = None
    is_premium: bool = False
    image_id: str | None = None


# ── Top-level envelope ────────────────────────────────────────────────────────


class TodoistWebhookEvent(BaseModel):
    event_name: str
    user_id: str
    # Kept as raw dict; the worker validates into the correct typed submodel
    # after routing on event_name.
    event_data: dict[str, Any]
    initiator: TodoistInitiator
    version: str = "8"

    @property
    def is_task_event(self) -> bool:
        return self.event_name in TASK_EVENTS

    @property
    def is_comment_event(self) -> bool:
        return self.event_name in COMMENT_EVENTS

    @property
    def is_project_event(self) -> bool:
        return self.event_name in PROJECT_EVENTS

    def task_data(self) -> TaskEventData:
        return TaskEventData.model_validate(self.event_data)

    def comment_data(self) -> CommentEventData:
        return CommentEventData.model_validate(self.event_data)
