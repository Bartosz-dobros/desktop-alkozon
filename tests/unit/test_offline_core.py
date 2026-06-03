import tempfile
from pathlib import Path

import pytest

from desktop_alkozon.core.database import get_db, init_db, set_db_path
from desktop_alkozon.core.outbox import (
    count_failed,
    count_pending,
    enqueue,
    get_by_id,
    get_failed,
    get_pending,
    mark_completed,
    mark_failed,
    mark_in_progress,
    revert_to_pending,
)
from desktop_alkozon.core.repository import (
    get_all_deliveries,
    get_all_inventory_products,
    get_all_inventory_raw_materials,
    get_all_job_offers,
    get_all_replenishments,
    get_all_users,
    get_sync_status,
    get_user,
    set_sync_status,
    upsert_deliveries,
    upsert_inventory,
    upsert_job_offers,
    upsert_replenishments,
    upsert_users,
)


@pytest.fixture
def db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    set_db_path(path)
    yield path
    Path(path).unlink(missing_ok=True)
    set_db_path(None)


@pytest.fixture
async def initialized_db(db_path):
    await init_db(db_path)
    return db_path


class TestDatabase:
    async def test_init_creates_tables(self, db_path):
        await init_db(db_path)
        async with get_db(db_path) as db:
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [row["name"] async for row in cursor]
        expected = [
            "announcements",
            "deliveries",
            "inventory_products",
            "inventory_raw_materials",
            "job_offers",
            "local_user",
            "outbox",
            "replenishments",
            "sync_status",
            "users",
        ]
        for t in expected:
            assert t in tables, f"Missing table: {t}"

    async def test_init_is_idempotent(self, db_path):
        await init_db(db_path)
        await init_db(db_path)
        async with get_db(db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) as cnt FROM sqlite_master")
            row = await cursor.fetchone()
            assert row["cnt"] > 0

    async def test_get_db_commits_on_exit(self, db_path):
        await init_db(db_path)
        async with get_db(db_path) as db:
            await db.execute(
                "INSERT INTO sync_status (source, status) VALUES (?, ?)",
                ("test", "synced"),
            )
        async with get_db(db_path) as db:
            cursor = await db.execute(
                "SELECT status FROM sync_status WHERE source = ?", ("test",)
            )
            row = await cursor.fetchone()
            assert row["status"] == "synced"


class TestRepository:
    async def test_upsert_users_inserts_new(self, initialized_db):
        users = [
            {
                "id": 1,
                "email": "a@test.com",
                "role": "MANAGER",
                "active": True,
                "courier": False,
            },
            {
                "id": 2,
                "email": "b@test.com",
                "role": "EMPLOYEE",
                "active": True,
                "courier": True,
            },
        ]
        await upsert_users(users, initialized_db)
        result = await get_all_users(initialized_db)
        assert len(result) == 2
        assert result[0]["email"] in ("a@test.com", "b@test.com")

    async def test_upsert_users_updates_existing(self, initialized_db):
        await upsert_users(
            [
                {
                    "id": 1,
                    "email": "old@test.com",
                    "role": "GUEST",
                    "active": True,
                    "courier": False,
                }
            ],
            initialized_db,
        )
        await upsert_users(
            [
                {
                    "id": 1,
                    "email": "new@test.com",
                    "role": "MANAGER",
                    "active": True,
                    "courier": False,
                }
            ],
            initialized_db,
        )
        user = await get_user(1, initialized_db)
        assert user["email"] == "new@test.com"
        assert user["role"] == "MANAGER"

    async def test_get_user_returns_none(self, initialized_db):
        user = await get_user(999, initialized_db)
        assert user is None

    async def test_upsert_job_offers(self, initialized_db):
        offers = [
            {
                "id": 1,
                "title": "Dev",
                "description": "desc",
                "status": "OPEN",
                "createdAt": "2024-01-01T00:00:00",
                "updatedAt": "2024-01-01T00:00:00",
            },
        ]
        await upsert_job_offers(offers, initialized_db)
        result = await get_all_job_offers(initialized_db)
        assert len(result) == 1
        assert result[0]["title"] == "Dev"

    async def test_upsert_inventory(self, initialized_db):
        products = [
            {"productId": 1, "name": "Beer", "quantity": 100, "warehouseZone": "A1"},
        ]
        raw_materials = [
            {"id": 1, "name": "Hops", "unit": "kg", "quantity": 50.0},
        ]
        await upsert_inventory(products, raw_materials, initialized_db)
        prods = await get_all_inventory_products(initialized_db)
        raws = await get_all_inventory_raw_materials(initialized_db)
        assert len(prods) == 1
        assert prods[0]["name"] == "Beer"
        assert len(raws) == 1
        assert raws[0]["name"] == "Hops"

    async def test_upsert_deliveries(self, initialized_db):
        deliveries = [
            {
                "id": 1,
                "orderId": 10,
                "status": "PENDING",
                "customerEmail": "c@test.com",
                "deliveryDetails": {"addr": "street"},
                "courierEmail": None,
            },
        ]
        await upsert_deliveries(deliveries, initialized_db)
        result = await get_all_deliveries(initialized_db)
        assert len(result) == 1
        assert result[0]["status"] == "PENDING"

    async def test_upsert_replenishments(self, initialized_db):
        repls = [
            {
                "id": 1,
                "note": "restock",
                "status": "OPEN",
                "createdAt": "2024-01-01T00:00:00",
                "lines": [{"productId": 1, "quantityDelta": 10}],
            },
        ]
        await upsert_replenishments(repls, initialized_db)
        result = await get_all_replenishments(initialized_db)
        assert len(result) == 1
        assert result[0]["note"] == "restock"

    async def test_sync_status_lifecycle(self, initialized_db):
        status = await get_sync_status("users", initialized_db)
        assert status is None
        await set_sync_status("users", "synced", initialized_db)
        status = await get_sync_status("users", initialized_db)
        assert status["status"] == "synced"
        assert status["source"] == "users"


class TestOutbox:
    async def test_enqueue_creates_entry(self, initialized_db):
        entry = await enqueue(
            entity_type="delivery",
            http_method="PATCH",
            endpoint="/deliveries/1/status",
            entity_id="1",
            request_body={"status": "IN_TRANSIT"},
            local_snapshot_before={"status": "PENDING"},
            db_path=initialized_db,
        )
        assert entry.id is not None
        assert entry.status == "pending"
        assert entry.entity_type == "delivery"

    async def test_get_pending_returns_ordered(self, initialized_db):
        await enqueue("test", "POST", "/test/1", db_path=initialized_db)
        await enqueue("test", "POST", "/test/2", db_path=initialized_db)
        pending = await get_pending(initialized_db)
        assert len(pending) == 2

    async def test_mark_completed(self, initialized_db):
        entry = await enqueue("test", "POST", "/test/1", db_path=initialized_db)
        await mark_completed(
            entry.id, response_body='{"ok": true}', db_path=initialized_db
        )
        updated = await get_by_id(entry.id, initialized_db)
        assert updated.status == "completed"

    async def test_mark_failed(self, initialized_db):
        entry = await enqueue("test", "POST", "/test/1", db_path=initialized_db)
        await mark_failed(entry.id, "Server error", db_path=initialized_db)
        updated = await get_by_id(entry.id, initialized_db)
        assert updated.status == "failed"
        assert updated.error_message == "Server error"

    async def test_mark_in_progress(self, initialized_db):
        entry = await enqueue("test", "POST", "/test/1", db_path=initialized_db)
        await mark_in_progress(entry.id, db_path=initialized_db)
        updated = await get_by_id(entry.id, initialized_db)
        assert updated.status == "in_progress"

    async def test_count_pending_and_failed(self, initialized_db):
        e1 = await enqueue("test", "POST", "/test/1", db_path=initialized_db)
        await enqueue("test", "POST", "/test/2", db_path=initialized_db)
        await mark_failed(e1.id, "error", db_path=initialized_db)
        assert await count_pending(initialized_db) == 1
        assert await count_failed(initialized_db) == 1

    async def test_get_failed_returns_descending(self, initialized_db):
        e1 = await enqueue("test", "POST", "/test/1", db_path=initialized_db)
        e2 = await enqueue("test", "POST", "/test/2", db_path=initialized_db)
        await mark_failed(e1.id, "err1", db_path=initialized_db)
        await mark_failed(e2.id, "err2", db_path=initialized_db)
        failed = await get_failed(initialized_db)
        assert len(failed) == 2

    async def test_get_by_id_returns_none(self, initialized_db):
        entry = await get_by_id("nonexistent", initialized_db)
        assert entry is None

    async def test_enqueue_without_optional_fields(self, initialized_db):
        entry = await enqueue(
            entity_type="user",
            http_method="DELETE",
            endpoint="/admin/users/5",
            db_path=initialized_db,
        )
        assert entry.request_body is None
        assert entry.local_snapshot_before is None

    async def test_revert_to_pending(self, initialized_db):
        entry = await enqueue("test", "POST", "/test", db_path=initialized_db)
        await mark_in_progress(entry.id, initialized_db)
        updated = await get_by_id(entry.id, initialized_db)
        assert updated.status == "in_progress"

        await revert_to_pending(entry.id, initialized_db)
        updated = await get_by_id(entry.id, initialized_db)
        assert updated.status == "pending"
