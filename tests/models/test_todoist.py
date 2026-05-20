import pytest
from pydantic import ValidationError

from src.models.todoist import (
    ALL_EVENTS,
    COMMENT_EVENTS,
    FILTER_EVENTS,
    LABEL_EVENTS,
    PROJECT_EVENTS,
    REMINDER_EVENTS,
    TASK_EVENTS,
    TodoistWebhookEvent,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

INITIATOR = {
    "id": "12345678",
    "full_name": "Test User",
    "email": "test@example.com",
    "is_premium": True,
    "image_id": None,
}

TASK_ADDED_PAYLOAD = {
    "event_name": "item:added",
    "user_id": "12345678",
    "event_data": {
        "id": "8765432109",
        "content": "Review Q2 report",
        "description": "",
        "project_id": "2349123456",
        "section_id": None,
        "parent_id": None,
        "labels": [],
        "priority": 2,
        "due": {
            "date": "2025-05-21",
            "timezone": None,
            "string": "tomorrow",
            "lang": "en",
            "is_recurring": False,
        },
        "added_at": "2025-05-20T10:30:00.000000Z",
        "updated_at": "2025-05-20T10:30:00.000000Z",
        "is_deleted": False,
        "creator_id": "12345678",
    },
    "initiator": INITIATOR,
    "version": "8",
}

TASK_WITH_DEADLINE_PAYLOAD = {
    **TASK_ADDED_PAYLOAD,
    "event_data": {
        **TASK_ADDED_PAYLOAD["event_data"],
        "deadline": {"date": "2025-05-31", "lang": "en"},
        "duration": {"amount": 30, "unit": "minute"},
    },
}

TASK_WITH_TIMED_DUE_PAYLOAD = {
    **TASK_ADDED_PAYLOAD,
    "event_data": {
        **TASK_ADDED_PAYLOAD["event_data"],
        "due": {
            "date": "2025-05-21T11:00:00",
            "timezone": "Australia/Sydney",
            "string": "tomorrow at 11am",
            "lang": "en",
            "is_recurring": False,
        },
    },
}

COMMENT_ADDED_PAYLOAD = {
    "event_name": "note:added",
    "user_id": "12345678",
    "event_data": {
        "id": "comment_abc123",
        "task_id": "8765432109",
        "content": "Plan this task",
        "posted_at": "2025-05-20T11:00:00.000000Z",
        "poster_id": "12345678",
        "attachment": None,
    },
    "initiator": INITIATOR,
    "version": "8",
}

# ── Task event tests ──────────────────────────────────────────────────────────


def test_task_added_parses():
    event = TodoistWebhookEvent.model_validate(TASK_ADDED_PAYLOAD)
    assert event.event_name == "item:added"
    assert event.is_task_event
    assert not event.is_comment_event

    task = event.task_data()
    assert task.id == "8765432109"
    assert task.content == "Review Q2 report"
    assert task.priority == 2
    assert task.due is not None
    assert task.due.date == "2025-05-21"
    assert not task.due.has_time
    assert task.deadline is None
    assert task.duration is None


def test_task_with_deadline_and_duration():
    event = TodoistWebhookEvent.model_validate(TASK_WITH_DEADLINE_PAYLOAD)
    task = event.task_data()
    assert task.deadline is not None
    assert task.deadline.date == "2025-05-31"
    assert task.duration is not None
    assert task.duration.amount == 30
    assert task.duration.unit == "minute"


def test_timed_due_date():
    event = TodoistWebhookEvent.model_validate(TASK_WITH_TIMED_DUE_PAYLOAD)
    task = event.task_data()
    assert task.due is not None
    assert task.due.has_time
    assert task.due.timezone == "Australia/Sydney"


def test_task_no_due():
    payload = {
        **TASK_ADDED_PAYLOAD,
        "event_data": {**TASK_ADDED_PAYLOAD["event_data"], "due": None},
    }
    assert TodoistWebhookEvent.model_validate(payload).task_data().due is None


# ── Comment event tests ───────────────────────────────────────────────────────


def test_comment_added_parses():
    event = TodoistWebhookEvent.model_validate(COMMENT_ADDED_PAYLOAD)
    assert event.event_name == "note:added"
    assert event.is_comment_event
    assert not event.is_task_event

    comment = event.comment_data()
    assert comment.task_id == "8765432109"
    assert comment.content == "Plan this task"
    assert comment.poster_id == "12345678"
    assert comment.attachment is None


# ── Event set tests ───────────────────────────────────────────────────────────


def test_all_event_sets_are_disjoint():
    sets = [TASK_EVENTS, COMMENT_EVENTS, PROJECT_EVENTS, LABEL_EVENTS,
            FILTER_EVENTS, REMINDER_EVENTS]
    for i, a in enumerate(sets):
        for b in sets[i + 1:]:
            assert a.isdisjoint(b), f"Overlapping event sets: {a & b}"


def test_all_events_union():
    expected = (TASK_EVENTS | COMMENT_EVENTS | PROJECT_EVENTS
                | LABEL_EVENTS | FILTER_EVENTS | REMINDER_EVENTS)
    assert ALL_EVENTS == expected


def test_known_event_names_covered():
    known = {
        "item:added", "item:updated", "item:completed", "item:uncompleted", "item:deleted",
        "note:added", "note:updated", "note:deleted",
        "project:added", "project:updated", "project:deleted",
        "project:archived", "project:unarchived",
        "label:added", "label:updated", "label:deleted",
        "filter:added", "filter:updated", "filter:deleted",
        "reminder:fired",
    }
    assert known == ALL_EVENTS


# ── Validation tests ──────────────────────────────────────────────────────────


def test_missing_event_name_raises():
    bad = {**TASK_ADDED_PAYLOAD}
    del bad["event_name"]
    with pytest.raises(ValidationError):
        TodoistWebhookEvent.model_validate(bad)


def test_initiator_fields():
    event = TodoistWebhookEvent.model_validate(TASK_ADDED_PAYLOAD)
    assert event.initiator.full_name == "Test User"
    assert event.initiator.email == "test@example.com"
