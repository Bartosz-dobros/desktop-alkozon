import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from desktop_alkozon.core.database import get_db


@dataclass
class OutboxEntry:
    id: str
    entity_type: str
    entity_id: str | None = None
    http_method: str = "POST"
    endpoint: str = ""
    request_body: str | None = None
    local_snapshot_before: str | None = None
    created_at: datetime | None = None
    retry_count: int = 0
    max_retries: int = 5
    status: str = "pending"
    error_message: str | None = None
    completed_at: datetime | None = None


def _row_to_entry(row: dict[str, Any]) -> OutboxEntry:
    return OutboxEntry(
        id=row["id"],
        entity_type=row["entity_type"],
        entity_id=row.get("entity_id"),
        http_method=row["http_method"],
        endpoint=row["endpoint"],
        request_body=row.get("request_body"),
        local_snapshot_before=row.get("local_snapshot_before"),
        created_at=row.get("created_at"),
        retry_count=row.get("retry_count", 0),
        max_retries=row.get("max_retries", 5),
        status=row.get("status", "pending"),
        error_message=row.get("error_message"),
        completed_at=row.get("completed_at"),
    )


async def enqueue(
    entity_type: str,
    http_method: str,
    endpoint: str,
    entity_id: str | None = None,
    request_body: dict[str, Any] | None = None,
    local_snapshot_before: dict[str, Any] | None = None,
    db_path: str | None = None,
) -> OutboxEntry:
    entry_id = str(uuid.uuid4())
    now = datetime.now(UTC)
    body_json = json.dumps(request_body) if request_body else None
    snapshot_json = json.dumps(local_snapshot_before) if local_snapshot_before else None

    async with get_db(db_path) as db:
        await db.execute(
            """INSERT INTO outbox (id, entity_type, entity_id, http_method,
                endpoint, request_body, local_snapshot_before, created_at, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')""",
            (
                entry_id,
                entity_type,
                entity_id,
                http_method,
                endpoint,
                body_json,
                snapshot_json,
                now.isoformat(),
            ),
        )

    return OutboxEntry(
        id=entry_id,
        entity_type=entity_type,
        entity_id=entity_id,
        http_method=http_method,
        endpoint=endpoint,
        request_body=body_json,
        local_snapshot_before=snapshot_json,
        created_at=now,
        status="pending",
    )


async def get_pending(db_path: str | None = None) -> list[OutboxEntry]:
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM outbox WHERE status = 'pending' ORDER BY created_at ASC"
        )
        rows = await cursor.fetchall()
        return [_row_to_entry(dict(row)) for row in rows]


async def get_failed(db_path: str | None = None) -> list[OutboxEntry]:
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM outbox WHERE status = 'failed' ORDER BY created_at DESC"
        )
        rows = await cursor.fetchall()
        return [_row_to_entry(dict(row)) for row in rows]


async def get_by_id(outbox_id: str, db_path: str | None = None) -> OutboxEntry | None:
    async with get_db(db_path) as db:
        cursor = await db.execute("SELECT * FROM outbox WHERE id = ?", (outbox_id,))
        row = await cursor.fetchone()
        return _row_to_entry(dict(row)) if row else None


async def mark_in_progress(outbox_id: str, db_path: str | None = None):
    async with get_db(db_path) as db:
        await db.execute(
            "UPDATE outbox SET status = 'in_progress' WHERE id = ?", (outbox_id,)
        )


async def mark_completed(
    outbox_id: str,
    response_body: str | None = None,
    db_path: str | None = None,
):
    now = datetime.now(UTC).isoformat()
    async with get_db(db_path) as db:
        await db.execute(
            """UPDATE outbox SET status = 'completed', completed_at = ?,
               error_message = ? WHERE id = ?""",
            (now, response_body, outbox_id),
        )


async def mark_failed(
    outbox_id: str,
    error_message: str,
    db_path: str | None = None,
):
    async with get_db(db_path) as db:
        await db.execute(
            """UPDATE outbox SET status = 'failed',
               error_message = ?, retry_count = retry_count + 1
               WHERE id = ?""",
            (error_message, outbox_id),
        )


async def revert_to_pending(outbox_id: str, db_path: str | None = None):
    async with get_db(db_path) as db:
        await db.execute(
            """UPDATE outbox SET status = 'pending',
               error_message = NULL, retry_count = 0
               WHERE id = ?""",
            (outbox_id,),
        )


async def increment_retry(outbox_id: str, db_path: str | None = None):
    async with get_db(db_path) as db:
        await db.execute(
            "UPDATE outbox SET retry_count = retry_count + 1 WHERE id = ?",
            (outbox_id,),
        )


async def count_pending(db_path: str | None = None) -> int:
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM outbox WHERE status = 'pending'"
        )
        row = await cursor.fetchone()
        return row["cnt"] if row else 0


async def count_failed(db_path: str | None = None) -> int:
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM outbox WHERE status = 'failed'"
        )
        row = await cursor.fetchone()
        return row["cnt"] if row else 0
