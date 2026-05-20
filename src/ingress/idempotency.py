import redis.asyncio as aioredis

from src.config import settings

_redis: aioredis.Redis | None = None
IDEMPOTENCY_TTL = 86_400  # 24 hours — covers delayed Todoist retries


async def init_redis() -> None:
    global _redis
    _redis = await aioredis.from_url(settings.redis_url, decode_responses=True)


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None


async def is_duplicate(event_key: str) -> bool:
    """Returns True if this key was already processed within the TTL window."""
    assert _redis is not None, "Redis not initialised — call init_redis() first"
    # SET NX returns None (no-op) if the key already existed
    result = await _redis.set(f"event:{event_key}", "1", nx=True, ex=IDEMPOTENCY_TTL)
    return result is None
