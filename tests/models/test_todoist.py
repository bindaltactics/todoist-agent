import pytest
from pydantic import ValidationError

from src.models.todoist import (
    COMMENT_EVENTS,
    TASK_EVENTS,
    TodoistWebhookEvent,
)

# Realistic payload shapes derived from the Todoist webhook format
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
        "completed_at": None,
        "updated_at": "2025-05-20T10:30:00.000000Z",
        "is_deleted": False,
        "creator_id": "12345678",
    },
    "initiator": {
        "id": "12345678",
        "full_name": "Test User",
        "email": "test@example.com",
        "is_premium": True,
        "image_id": None,
    },
    "version": "8",
}

TASK_ADDED_WITH_TIME_PAYLOAD = {
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
        "reactions": {},
    },
    "initiator": {
        "id": "12345678",
        "full_name": "Test User",
        "email": "test@example.com",
        "is_premium": True,
        "image_id": None,
    },
    "version": "8",
}


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


def test_task_with_time_due():
    event = TodoistWebhookEvent.model_validate(TASK_ADDED_WITH_TIME_PAYLOAD)
    task = event.task_data()
    assert task.due is not None
    assert task.due.has_time
    assert task.due.timezone == "Australia/Sydney"


def test_task_no_due_date():
    payload = {
        **TASK_ADDED_PAYLOAD,
        "event_data": {**TASK_ADDED_PAYLOAD["event_data"], "due": None},
    }
    event = TodoistWebhookEvent.model_validate(payload)
    assert event.task_data().due is None


def test_comment_added_parses():
    event = TodoistWebhookEvent.model_validate(COMMENT_ADDED_PAYLOAD)
    assert event.event_name == "note:added"
    assert event.is_comment_event
    assert not event.is_task_event

    comment = event.comment_data()
    assert comment.task_id == "8765432109"
    assert comment.content == "Plan this task"


def test_event_name_sets_are_disjoint():
    assert TASK_EVENTS.isdisjoint(COMMENT_EVENTS)


def test_missing_required_field_raises():
    bad = {**TASK_ADDED_PAYLOAD}
    del bad["event_name"]
    with pytest.raises(ValidationError):
        TodoistWebhookEvent.model_validate(bad)


def test_initiator_fields():
    event = TodoistWebhookEvent.model_validate(TASK_ADDED_PAYLOAD)
    assert event.initiator.full_name == "Test User"
    assert event.initiator.email == "test@example.com"
