import base64
import hashlib
import hmac

from fastapi import HTTPException, Request

from src.config import settings


async def verify_todoist_signature(request: Request) -> bytes:
    """Verifies X-Todoist-Hmac-SHA256 and returns the raw body."""
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

    return body
