import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response

from src.ingress.idempotency import close_redis, init_redis, is_duplicate
from src.ingress.queue import enqueue, setup_queue
from src.ingress.signature import verify_todoist_signature
from src.state.db import close_pool, get_pool

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = await get_pool()
    await setup_queue(pool)
    await init_redis()
    yield
    await close_pool()
    await close_redis()


app = FastAPI(title="todoist-agent ingress", lifespan=lifespan)


@app.post("/webhook/todoist")
async def todoist_webhook(request: Request) -> Response:
    body, delivery_id = await verify_todoist_signature(request)

    if await is_duplicate(delivery_id):
        logger.info("Duplicate delivery %s, skipping", delivery_id)
        return Response(status_code=200)

    payload = json.loads(body)
    pool = await get_pool()
    await enqueue(pool, payload)
    return Response(status_code=200)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
