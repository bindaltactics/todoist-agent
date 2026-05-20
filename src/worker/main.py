import asyncio
import logging

import asyncpg

from src.ingress.queue import QUEUE_NAME
from src.state.db import close_pool, get_pool

logger = logging.getLogger(__name__)

VISIBILITY_TIMEOUT = 30  # seconds before unacked message reappears for retry
BATCH_SIZE = 10
POLL_INTERVAL = 1.0


async def process_message(pool: asyncpg.Pool, row: asyncpg.Record) -> None:
    msg_id: int = row["msg_id"]
    payload: dict = dict(row["message"])
    event_name = payload.get("event_name", "unknown")

    try:
        logger.info("Processing %s (msg_id=%s)", event_name, msg_id)
        # TODO: dispatch to LangGraph orchestrator
        await pool.execute("SELECT pgmq.delete($1, $2)", QUEUE_NAME, msg_id)
    except Exception:
        logger.exception("Failed to process msg_id=%s — will retry after visibility timeout", msg_id)


async def poll_loop() -> None:
    pool = await get_pool()
    logger.info("Worker started, polling queue '%s'", QUEUE_NAME)

    while True:
        try:
            rows = await pool.fetch(
                "SELECT * FROM pgmq.read($1, $2, $3)",
                QUEUE_NAME,
                VISIBILITY_TIMEOUT,
                BATCH_SIZE,
            )
            for row in rows:
                await process_message(pool, row)
        except Exception:
            logger.exception("Poll error")

        await asyncio.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    asyncio.run(poll_loop())
