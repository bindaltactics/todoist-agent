import base64
import hashlib
import hmac

from fastapi import HTTPException, Request

from src.config import settings


async def verify_todoist_signature(request: Request) -> tuple[bytes, str]:
    """
    Verifies X-Todoist-Hmac-SHA256 and returns (raw_body, delivery_id).

    delivery_id comes from X-Todoist-Delivery-ID when present (Todoist's
    official idempotency key); falls back to a SHA-256 of the body so the
    rest of the pipeline always has a stable dedup key.
    """
    signature = request.headers.get("X-Todoist-Hmac-SHA256")
    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature")

    body = await request.body()
    expected = base64.b64encode(
        hmac.new(
            settings.todoist_client_secret.encode(),
            body,
            hashlib.sha256,
        ).digest()
    ).decode()

    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=401, detail="Invalid signature")

    delivery_id = (
        request.headers.get("X-Todoist-Delivery-ID")
        or hashlib.sha256(body).hexdigest()
    )
    return body, delivery_id
