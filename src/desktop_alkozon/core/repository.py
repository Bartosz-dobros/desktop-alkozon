import json
from typing import Any

from desktop_alkozon.core.database import get_db


def _get(d: dict, *keys):
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return None


async def upsert_users(users: list[dict[str, Any]], db_path: str | None = None):
    async with get_db(db_path) as db:
        for user in users:
            await db.execute(
                """INSERT INTO users (id, email, role, active, courier,
                    age_confirmed_at, first_name, last_name, phone, synced_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                   ON CONFLICT(id) DO UPDATE SET
                    email=excluded.email, role=excluded.role,
                    active=excluded.active, courier=excluded.courier,
                    age_confirmed_at=excluded.age_confirmed_at,
                    first_name=excluded.first_name,
                    last_name=excluded.last_name,
                    phone=excluded.phone,
                    synced_at=CURRENT_TIMESTAMP""",
                (
                    user.get("id"),
                    user.get("email"),
                    user.get("role"),
                    int(user.get("active", True)),
                    int(user.get("courier", False)),
                    _get(user, "ageConfirmedAt", "age_confirmed_at"),
                    _get(user, "firstName", "first_name"),
                    _get(user, "lastName", "last_name"),
                    user.get("phone"),
                ),
            )


async def get_all_users(db_path: str | None = None) -> list[dict[str, Any]]:
    async with get_db(db_path) as db:
        cursor = await db.execute("SELECT * FROM users")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_user(user_id: int, db_path: str | None = None) -> dict[str, Any] | None:
    async with get_db(db_path) as db:
        cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def upsert_job_offers(offers: list[dict[str, Any]], db_path: str | None = None):
    async with get_db(db_path) as db:
        for offer in offers:
            await db.execute(
                """INSERT INTO job_offers (id, title, description, status,
                    created_at, updated_at, synced_at)
                   VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                   ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title, description=excluded.description,
                    status=excluded.status, created_at=excluded.created_at,
                    updated_at=excluded.updated_at, synced_at=CURRENT_TIMESTAMP""",
                (
                    offer.get("id"),
                    offer.get("title"),
                    offer.get("description"),
                    offer.get("status"),
                    _get(offer, "createdAt", "created_at"),
                    _get(offer, "updatedAt", "updated_at"),
                ),
            )


async def get_all_job_offers(db_path: str | None = None) -> list[dict[str, Any]]:
    async with get_db(db_path) as db:
        cursor = await db.execute("SELECT * FROM job_offers ORDER BY created_at DESC")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def upsert_inventory(
    products: list[dict[str, Any]],
    raw_materials: list[dict[str, Any]],
    db_path: str | None = None,
):
    async with get_db(db_path) as db:
        for p in products:
            await db.execute(
                """INSERT INTO inventory_products (product_id, name, quantity,
                    warehouse_zone, synced_at)
                   VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                   ON CONFLICT(product_id) DO UPDATE SET
                    name=excluded.name, quantity=excluded.quantity,
                    warehouse_zone=excluded.warehouse_zone,
                    synced_at=CURRENT_TIMESTAMP""",
                (
                    _get(p, "productId", "product_id"),
                    p.get("name"),
                    p.get("quantity", 0),
                    _get(p, "warehouseZone", "warehouse_zone"),
                ),
            )
        for rm in raw_materials:
            await db.execute(
                """INSERT INTO inventory_raw_materials (id, name, unit, quantity, synced_at)
                   VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                   ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name, unit=excluded.unit,
                    quantity=excluded.quantity, synced_at=CURRENT_TIMESTAMP""",
                (
                    rm.get("id"),
                    rm.get("name"),
                    rm.get("unit"),
                    rm.get("quantity", 0),
                ),
            )


async def get_all_inventory_products(
    db_path: str | None = None,
) -> list[dict[str, Any]]:
    async with get_db(db_path) as db:
        cursor = await db.execute("SELECT * FROM inventory_products")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_all_inventory_raw_materials(
    db_path: str | None = None,
) -> list[dict[str, Any]]:
    async with get_db(db_path) as db:
        cursor = await db.execute("SELECT * FROM inventory_raw_materials")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def update_inventory_product_quantity(
    product_id: int, delta: int, db_path: str | None = None
):
    async with get_db(db_path) as db:
        await db.execute(
            "UPDATE inventory_products SET quantity = quantity + ? WHERE product_id = ?",
            (delta, product_id),
        )


async def update_inventory_raw_material_quantity(
    raw_material_id: int, delta: float, db_path: str | None = None
):
    async with get_db(db_path) as db:
        await db.execute(
            "UPDATE inventory_raw_materials SET quantity = quantity + ? WHERE id = ?",
            (delta, raw_material_id),
        )


async def upsert_deliveries(
    deliveries: list[dict[str, Any]], db_path: str | None = None
):
    async with get_db(db_path) as db:
        for d in deliveries:
            await db.execute(
                """INSERT INTO deliveries (id, order_id, custom_order_id,
                    custom_order, client_order_number, courier_id, courier_email,
                    status, customer_email, delivery_details, started_at,
                    delivered_at, synced_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                   ON CONFLICT(id) DO UPDATE SET
                    order_id=excluded.order_id,
                    custom_order_id=excluded.custom_order_id,
                    custom_order=excluded.custom_order,
                    client_order_number=excluded.client_order_number,
                    courier_id=excluded.courier_id,
                    courier_email=excluded.courier_email,
                    status=excluded.status,
                    customer_email=excluded.customer_email,
                    delivery_details=excluded.delivery_details,
                    started_at=excluded.started_at,
                    delivered_at=excluded.delivered_at,
                    synced_at=CURRENT_TIMESTAMP""",
                (
                    d.get("id"),
                    _get(d, "orderId", "order_id"),
                    _get(d, "customOrderId", "custom_order_id"),
                    int(d.get("customOrder", d.get("custom_order", False))),
                    _get(d, "clientOrderNumber", "client_order_number"),
                    _get(d, "courierId", "courier_id"),
                    _get(d, "courierEmail", "courier_email"),
                    d.get("status"),
                    _get(d, "customerEmail", "customer_email"),
                    json.dumps(
                        d.get("deliveryDetails") or d.get("delivery_details") or {}
                    ),
                    _get(d, "startedAt", "started_at"),
                    _get(d, "deliveredAt", "delivered_at"),
                ),
            )


async def get_all_deliveries(db_path: str | None = None) -> list[dict[str, Any]]:
    async with get_db(db_path) as db:
        cursor = await db.execute("SELECT * FROM deliveries")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def upsert_replenishments(
    replenishments: list[dict[str, Any]], db_path: str | None = None
):
    async with get_db(db_path) as db:
        for r in replenishments:
            await db.execute(
                """INSERT INTO replenishments (id, note, status, created_at, lines, synced_at)
                   VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                   ON CONFLICT(id) DO UPDATE SET
                    note=excluded.note, status=excluded.status,
                    created_at=excluded.created_at, lines=excluded.lines,
                    synced_at=CURRENT_TIMESTAMP""",
                (
                    r.get("id"),
                    r.get("note"),
                    r.get("status"),
                    _get(r, "createdAt", "created_at"),
                    json.dumps(r.get("lines", [])),
                ),
            )


async def get_all_replenishments(
    db_path: str | None = None,
) -> list[dict[str, Any]]:
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM replenishments ORDER BY created_at DESC"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def upsert_announcements(
    announcements: list[dict[str, Any]], db_path: str | None = None
):
    async with get_db(db_path) as db:
        for a in announcements:
            await db.execute(
                """INSERT INTO announcements (id, title, content, published_at,
                    created_by, created_at, synced_at)
                   VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                   ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title, content=excluded.content,
                    published_at=excluded.published_at,
                    created_by=excluded.created_by, created_at=excluded.created_at,
                    synced_at=CURRENT_TIMESTAMP""",
                (
                    a.get("id"),
                    a.get("title"),
                    a.get("content"),
                    _get(a, "publishedAt", "published_at"),
                    _get(a, "createdBy", "created_by"),
                    _get(a, "createdAt", "created_at"),
                ),
            )


async def get_all_announcements(
    db_path: str | None = None,
) -> list[dict[str, Any]]:
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM announcements ORDER BY created_at DESC"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_sync_status(
    source: str, db_path: str | None = None
) -> dict[str, Any] | None:
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM sync_status WHERE source = ?", (source,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def set_sync_status(source: str, status: str, db_path: str | None = None):
    async with get_db(db_path) as db:
        await db.execute(
            """INSERT INTO sync_status (source, last_synced_at, status)
               VALUES (?, CURRENT_TIMESTAMP, ?)
               ON CONFLICT(source) DO UPDATE SET
                last_synced_at=CURRENT_TIMESTAMP, status=excluded.status""",
            (source, status),
        )


async def get_all_sync_statuses(db_path: str | None = None) -> list[dict[str, Any]]:
    async with get_db(db_path) as db:
        cursor = await db.execute("SELECT * FROM sync_status")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
