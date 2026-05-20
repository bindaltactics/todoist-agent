import base64
import hashlib
import hmac
import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.ingress.app import app

SECRET = "test-secret"


def sign(body: bytes) -> str:
    digest = hmac.new(SECRET.encode(), body, hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


@pytest.fixture
def client():
    with (
        patch("src.ingress.app.get_pool", new_callable=AsyncMock),
        patch("src.ingress.app.setup_queue", new_callable=AsyncMock),
        patch("src.ingress.app.init_redis", new_callable=AsyncMock),
        patch("src.ingress.app.close_pool", new_callable=AsyncMock),
        patch("src.ingress.app.close_redis", new_callable=AsyncMock),
    ):
        with TestClient(app) as c:
            yield c


def test_health(client):
    assert client.get("/health").status_code == 200


def test_missing_signature(client):
    assert client.post("/webhook/todoist", json={"x": 1}).status_code == 401


def test_invalid_signature(client):
    body = json.dumps({"x": 1}).encode()
    resp = client.post(
        "/webhook/todoist",
        content=body,
        headers={"X-Todoist-Hmac-SHA256": "wrong"},
    )
    assert resp.status_code == 401


def test_duplicate_skipped(client):
    payload = {"event_name": "item:added", "event_data": {"id": "123"}}
    body = json.dumps(payload).encode()

    with (
        patch("src.ingress.app.is_duplicate", new_callable=AsyncMock, return_value=True),
        patch("src.ingress.app.enqueue", new_callable=AsyncMock) as mock_enqueue,
    ):
        resp = client.post(
            "/webhook/todoist",
            content=body,
            headers={"X-Todoist-Hmac-SHA256": sign(body)},
        )
    assert resp.status_code == 200
    mock_enqueue.assert_not_called()


def test_valid_event_enqueued(client):
    payload = {"event_name": "item:added", "event_data": {"id": "456"}}
    body = json.dumps(payload).encode()

    with (
        patch("src.ingress.app.is_duplicate", new_callable=AsyncMock, return_value=False),
        patch("src.ingress.app.enqueue", new_callable=AsyncMock) as mock_enqueue,
    ):
        resp = client.post(
            "/webhook/todoist",
            content=body,
            headers={"X-Todoist-Hmac-SHA256": sign(body)},
        )
    assert resp.status_code == 200
    mock_enqueue.assert_called_once()
