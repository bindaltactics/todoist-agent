import asyncio
import logging

import asyncpg
from pydantic import ValidationError

from src.ingress.queue import QUEUE_NAME
from src.models.todoist import TodoistWebhookEvent
from src.state.db import close_pool, get_pool

logger = logging.getLogger(__name__)

VISIBILITY_TIMEOUT = 30  # seconds before unacked message reappears for retry
BATCH_SIZE = 10
POLL_INTERVAL = 1.0


async def dispatch(event: TodoistWebhookEvent) -> None:
    """Route a validated event to the appropriate handler. Stubbed until orchestrator exists."""
    if event.is_task_event:
        task = event.task_data()
        logger.info(
            "Task event: %s  id=%s  title=%r  priority=%s  due=%s",
            event.event_name,
            task.id,
            task.content,
            task.priority,
            task.due.date if task.due else None,
        )
        # TODO: dispatch to LangGraph orchestrator → Router → Classifier
    elif event.is_comment_event:
        comment = event.comment_data()
        logger.info(
            "Comment event: %s  comment_id=%s  task_id=%s  author=%s",
            event.event_name,
            comment.id,
            comment.task_id,
            event.initiator.full_name,
        )
        # TODO: dispatch to LangGraph orchestrator → Router → Conversationalist
    else:
        logger.warning("Unknown event_name=%s — ignoring", event.event_name)


async def process_message(pool: asyncpg.Pool, row: asyncpg.Record) -> None:
    msg_id: int = row["msg_id"]
    raw: dict = dict(row["message"])

    try:
        event = TodoistWebhookEvent.model_validate(raw)
        await dispatch(event)
        await pool.execute("SELECT pgmq.delete($1, $2)", QUEUE_NAME, msg_id)
    except ValidationError as exc:
        # Bad payload — delete immediately so it doesn't block the queue forever
        logger.error("Invalid event payload for msg_id=%s: %s", msg_id, exc)
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
