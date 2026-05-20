import json

import asyncpg

QUEUE_NAME = "webhook_events"


async def setup_queue(pool: asyncpg.Pool) -> None:
    """Creates the pgmq queue if it doesn't already exist."""
    await pool.execute(
        """
        DO $$ BEGIN
            PERFORM pgmq.create($1);
        EXCEPTION WHEN OTHERS THEN NULL;
        END $$
        """,
        QUEUE_NAME,
    )


async def enqueue(pool: asyncpg.Pool, payload: dict) -> int:
    msg_id: int = await pool.fetchval(
        "SELECT pgmq.send($1, $2::jsonb)",
        QUEUE_NAME,
        json.dumps(payload),
    )
    return msg_id
