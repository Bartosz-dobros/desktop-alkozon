import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite

from desktop_alkozon.core.encryption import (
    clear_plain_file,
    decrypt_file,
    encrypt_file,
    encrypted_path_for,
)

_db_lock: asyncio.Lock | None = None


def _get_lock() -> asyncio.Lock:
    global _db_lock
    if _db_lock is None:
        _db_lock = asyncio.Lock()
    return _db_lock


async def _clear_plain_file_with_retry(path: str):
    for attempt in range(5):
        try:
            clear_plain_file(path)
            return
        except PermissionError:
            if attempt < 4:
                await asyncio.sleep(0.1 * (attempt + 1))
            else:
                raise


MIGRATIONS = [
    "ALTER TABLE local_user ADD COLUMN two_fa_code TEXT",
    "CREATE TABLE IF NOT EXISTS app_config (key TEXT PRIMARY KEY, value TEXT NOT NULL)",
]


async def _run_migrations(db_path: str):
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("PRAGMA table_info(local_user)")
        columns = {row["name"] for row in await cursor.fetchall()}
        for migration in MIGRATIONS:
            col_name = migration.split()[-2]
            if col_name not in columns:
                await db.execute(migration)
        await db.commit()


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS local_user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    device_id TEXT,
    last_login TIMESTAMP,
    two_fa_code TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    email TEXT,
    role TEXT,
    active INTEGER DEFAULT 1,
    courier INTEGER DEFAULT 0,
    age_confirmed_at TIMESTAMP,
    first_name TEXT,
    last_name TEXT,
    phone TEXT,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS job_offers (
    id INTEGER PRIMARY KEY,
    title TEXT,
    description TEXT,
    status TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inventory_products (
    product_id INTEGER PRIMARY KEY,
    name TEXT,
    quantity INTEGER DEFAULT 0,
    warehouse_zone TEXT,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inventory_raw_materials (
    id INTEGER PRIMARY KEY,
    name TEXT,
    unit TEXT,
    quantity REAL DEFAULT 0.0,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS deliveries (
    id INTEGER PRIMARY KEY,
    order_id INTEGER,
    custom_order_id INTEGER,
    custom_order INTEGER DEFAULT 0,
    client_order_number TEXT,
    courier_id INTEGER,
    courier_email TEXT,
    status TEXT,
    customer_email TEXT,
    delivery_details TEXT,
    started_at TIMESTAMP,
    delivered_at TIMESTAMP,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS replenishments (
    id INTEGER PRIMARY KEY,
    note TEXT,
    status TEXT,
    created_at TIMESTAMP,
    lines TEXT,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS announcements (
    id INTEGER PRIMARY KEY,
    title TEXT,
    content TEXT,
    published_at TIMESTAMP,
    created_by INTEGER,
    created_at TIMESTAMP,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sync_status (
    source TEXT PRIMARY KEY,
    last_synced_at TIMESTAMP,
    status TEXT DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS outbox (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    http_method TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    request_body TEXT,
    local_snapshot_before TEXT,
    created_at TIMESTAMP NOT NULL,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 5,
    status TEXT DEFAULT 'pending',
    error_message TEXT,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def get_default_db_path() -> str:
    env_path = os.environ.get("ALKOZON_DB_PATH")
    if env_path:
        return env_path
    db_dir = Path.home() / ".alkozon"
    db_dir.mkdir(parents=True, exist_ok=True)
    return str(db_dir / "alkozon_offline.db")


_db_path: str | None = None


def set_db_path(path: str):
    global _db_path
    _db_path = path


def get_db_path() -> str:
    return _db_path or get_default_db_path()


async def init_db(db_path: str | None = None):
    async with _get_lock():
        path = db_path or get_db_path()
        enc_path = encrypted_path_for(path)

        if os.path.exists(enc_path):
            await decrypt_file(enc_path, path)
            await _run_migrations(path)
            return

        if os.path.exists(path):
            os.remove(path)

        async with aiosqlite.connect(path) as db:
            db.row_factory = aiosqlite.Row
            await db.executescript(SCHEMA_SQL)
            await db.commit()

        await encrypt_file(path, enc_path)
        await _clear_plain_file_with_retry(path)


@asynccontextmanager
async def get_db(db_path: str | None = None):
    async with _get_lock():
        path = db_path or get_db_path()
        enc_path = encrypted_path_for(path)

        if os.path.exists(enc_path):
            await decrypt_file(enc_path, path)
            await _run_migrations(path)

        async with aiosqlite.connect(path) as db:
            db.row_factory = aiosqlite.Row
            yield db
            await db.commit()

        await encrypt_file(path, enc_path)
        await _clear_plain_file_with_retry(path)
