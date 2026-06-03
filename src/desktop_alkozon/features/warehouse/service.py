import contextlib
import json
from datetime import datetime

from desktop_alkozon.core import repository
from desktop_alkozon.core.auth import auth_service
from desktop_alkozon.core.database import get_db_path
from desktop_alkozon.core.exceptions import OfflineError
from desktop_alkozon.core.outbox import enqueue
from desktop_alkozon.models.api_models import (
    InventoryOverviewResponse,
    InventoryProductRow,
    InventoryRawRow,
    ReplenishmentLine,
    WarehouseReplenishment,
)
from desktop_alkozon.services.api_client import api_client


def _parse_line(data: dict) -> ReplenishmentLine:
    product = data.get("product")
    if product:
        product_id = product.get("id")
        product_name = product.get("name")
    else:
        product_id = data.get("productId")
        product_name = data.get("productName")
    raw_material = data.get("rawMaterial")
    if raw_material:
        raw_material_id = raw_material.get("id")
        raw_material_name = raw_material.get("name")
    else:
        raw_material_id = data.get("rawMaterialId")
        raw_material_name = data.get("rawMaterialName")
    return ReplenishmentLine(
        id=data.get("id", 0),
        productId=product_id,
        rawMaterialId=raw_material_id,
        quantityDelta=data.get("quantityDelta", 0),
        productName=product_name,
        rawMaterialName=raw_material_name,
    )


def _parse_order(data: dict) -> WarehouseReplenishment:
    raw_lines = data.get("lines") or []
    lines = [_parse_line(ln) for ln in raw_lines]
    created_raw = data.get("createdAt")
    if isinstance(created_raw, str):
        try:
            created_at = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
        except ValueError:
            created_at = datetime.now()
    else:
        created_at = created_raw or datetime.now()
    return WarehouseReplenishment(
        id=data.get("id", 0),
        status=data.get("status", "PENDING"),
        note=data.get("note"),
        createdAt=created_at,
        lines=lines,
    )


DEMO_REPLENISHMENTS = [
    WarehouseReplenishment(
        id=1,
        status="PENDING",
        note="Monthly stock refill",
        createdAt=datetime(2025, 5, 20, 10, 30, 0),
        lines=[
            ReplenishmentLine(
                id=1,
                productId=1,
                quantityDelta=200,
                productName="Demo Vodka 500ml",
            ),
            ReplenishmentLine(
                id=2,
                productId=2,
                quantityDelta=100,
                productName="Demo Whisky 700ml",
            ),
        ],
    ),
    WarehouseReplenishment(
        id=2,
        status="RECEIVED",
        note="Emergency order",
        createdAt=datetime(2025, 5, 15, 14, 0, 0),
        lines=[
            ReplenishmentLine(
                id=3,
                productId=1,
                quantityDelta=50,
                productName="Demo Vodka 500ml",
            ),
        ],
    ),
]

_session_cache: list[WarehouseReplenishment] = []


class WarehouseService:
    async def get_all_items(self) -> InventoryOverviewResponse | None:
        try:
            response = await api_client.get("/inventory")
            if isinstance(response, dict):
                with contextlib.suppress(Exception):
                    await repository.upsert_inventory(
                        response.get("products", []),
                        response.get("rawMaterials", []),
                        get_db_path(),
                    )
            print(
                f"[Warehouse] GET /inventory raw: keys={list(response.keys()) if isinstance(response, dict) else type(response).__name__}, "
                f"rawMaterials count={len(response.get('rawMaterials', [])) if isinstance(response, dict) else 'N/A'}"
            )
            parsed = InventoryOverviewResponse(**response)
            print(
                f"[Warehouse] GET /inventory parsed: products={len(parsed.products)}, rawMaterials={len(parsed.rawMaterials)}"
            )
            return parsed
        except OfflineError:
            db_path = get_db_path()
            products = await repository.get_all_inventory_products(db_path)
            raw_materials = await repository.get_all_inventory_raw_materials(db_path)
            return InventoryOverviewResponse(
                products=[
                    InventoryProductRow(
                        productId=p["product_id"],
                        name=p["name"],
                        quantity=p["quantity"],
                        warehouseZone=p.get("warehouse_zone"),
                    )
                    for p in products
                ],
                rawMaterials=[
                    InventoryRawRow(
                        id=rm["id"],
                        name=rm["name"],
                        unit=rm["unit"],
                        quantity=rm["quantity"],
                    )
                    for rm in raw_materials
                ],
            )
        except Exception as e:
            status = getattr(e, "response", None)
            code = status.status_code if status else "?"
            print(
                f"[Warehouse] GET /inventory failed: HTTP {code} | {type(e).__name__}: {e}"
            )
            import traceback

            traceback.print_exc()
            if auth_service.is_demo_mode():
                print("[Warehouse] Falling back to demo data")
                return InventoryOverviewResponse(
                    products=[
                        InventoryProductRow(
                            productId=1,
                            name="Demo Vodka 500ml",
                            quantity=100,
                            warehouseZone="A1",
                        ),
                        InventoryProductRow(
                            productId=2,
                            name="Demo Whisky 700ml",
                            quantity=50,
                            warehouseZone="B2",
                        ),
                        InventoryProductRow(
                            productId=3,
                            name="Demo Gin 700ml",
                            quantity=30,
                            warehouseZone="A1",
                        ),
                    ],
                    rawMaterials=[
                        InventoryRawRow(id=1, name="Barley", unit="kg", quantity=500.0),
                        InventoryRawRow(id=2, name="Grapes", unit="kg", quantity=300.0),
                    ],
                )
            return None

    def add_new_item_sync(
        self, product_id: int, quantity_delta: int, note: str | None = None
    ):
        if auth_service.is_demo_mode():
            return WarehouseReplenishment(
                id=99,
                status="PENDING",
                note=note,
                createdAt=datetime.now(),
                lines=[
                    ReplenishmentLine(
                        id=99,
                        productId=product_id,
                        quantityDelta=quantity_delta,
                        productName=f"Product #{product_id}",
                    )
                ],
            )
        return None

    async def add_new_item(
        self, product_id: int, quantity_delta: int, note: str | None = None
    ) -> WarehouseReplenishment | None:
        global _session_cache
        try:
            payload = {
                "lines": [{"productId": product_id, "quantityDelta": quantity_delta}],
            }
            if note:
                payload["note"] = note
            response = await api_client.post("/warehouse/replenishment", payload)
            print(
                f"[Warehouse] POST /warehouse/replenishment response keys={list(response.keys()) if isinstance(response, dict) else type(response).__name__}, status={response.get('status')!r}"
            )
            try:
                order = _parse_order(response)
                _session_cache.insert(0, order)
                return order
            except Exception as pe:
                print(f"[Warehouse] POST succeeded (201) but _parse_order failed: {pe}")
                fallback = WarehouseReplenishment(
                    id=response.get("id", 0),
                    status=response.get("status", "PENDING"),
                    note=note,
                    createdAt=datetime.now(),
                    lines=[
                        ReplenishmentLine(
                            id=0,
                            productId=product_id,
                            quantityDelta=quantity_delta,
                            productName=f"Product #{product_id}",
                        )
                    ],
                )
                _session_cache.insert(0, fallback)
                return fallback
        except json.JSONDecodeError as je:
            doc = getattr(je, "doc", None)
            print(
                f"[Warehouse] POST /warehouse/replenishment: HTTP 201 but JSON corrupt at pos {je.pos}"
            )
            if doc and "{" in doc:
                first = doc.find("{")
                depth = 0
                for i in range(first, len(doc)):
                    if doc[i] == "{":
                        depth += 1
                    elif doc[i] == "}":
                        depth -= 1
                        if depth == 0:
                            try:
                                data = json.loads(doc[first : i + 1])
                                order = _parse_order(data)
                                print(
                                    f"[Warehouse] Extracted valid order id={order.id}"
                                )
                                _session_cache.insert(0, order)
                                return order
                            except Exception:
                                pass
                            break
            fallback = WarehouseReplenishment(
                id=0,
                status="PENDING",
                note=note,
                createdAt=datetime.now(),
                lines=[
                    ReplenishmentLine(
                        id=0,
                        productId=product_id,
                        quantityDelta=quantity_delta,
                        productName=f"Product #{product_id}",
                    )
                ],
            )
            _session_cache.insert(0, fallback)
            return fallback
        except OfflineError:
            db_path = get_db_path()
            await enqueue(
                "replenishment",
                "POST",
                "/warehouse/replenishment",
                request_body=payload,
                db_path=db_path,
            )
            return None
        except Exception as e:
            status = getattr(e, "response", None)
            code = status.status_code if status else "?"
            body = ""
            if status is not None:
                try:
                    body = status.text[:500]
                except Exception:
                    body = "(unreadable)"
            print(f"[Warehouse] POST /warehouse/replenishment failed: HTTP {code}")
            if body:
                print(f"[Warehouse] Response body: {body}")
            print(f"[Warehouse] Exception type: {type(e).__name__}: {e}")
            if auth_service.is_demo_mode():
                return WarehouseReplenishment(
                    id=99,
                    status="PENDING",
                    note=note,
                    createdAt=datetime.now(),
                    lines=[
                        ReplenishmentLine(
                            id=99,
                            productId=product_id,
                            quantityDelta=quantity_delta,
                            productName=f"Product #{product_id}",
                        )
                    ],
                )
            return None

    async def update_item_quantity(
        self, item_id: int, delta: int
    ) -> InventoryProductRow | None:
        try:
            response = await api_client.patch(
                f"/inventory/products/{item_id}", {"delta": delta}
            )
            return InventoryProductRow(**response)
        except OfflineError:
            db_path = get_db_path()
            await repository.update_inventory_product_quantity(item_id, delta, db_path)
            await enqueue(
                "inventory",
                "PATCH",
                f"/inventory/products/{item_id}",
                entity_id=str(item_id),
                request_body={"delta": delta},
                db_path=db_path,
            )
            return None
        except Exception:
            return None

    async def update_raw_material(
        self, material_id: int, delta: int
    ) -> InventoryRawRow | None:
        try:
            response = await api_client.patch(
                f"/inventory/raw-materials/{material_id}", {"delta": delta}
            )
            return InventoryRawRow(**response)
        except OfflineError:
            db_path = get_db_path()
            await repository.update_inventory_raw_material_quantity(
                material_id, delta, db_path
            )
            await enqueue(
                "inventory",
                "PATCH",
                f"/inventory/raw-materials/{material_id}",
                entity_id=str(material_id),
                request_body={"delta": delta},
                db_path=db_path,
            )
            return None
        except Exception:
            return None

    async def get_replenishment_history(self) -> list[WarehouseReplenishment]:
        global _session_cache
        try:
            response = await api_client.get("/warehouse/replenishment")
            if isinstance(response, list):
                print(
                    f"[Warehouse] GET /warehouse/replenishment: {len(response)} orders returned"
                )
                if response:
                    sample = response[0]
                    print(
                        f"[Warehouse] First order keys: {list(sample.keys())}, lines count: {len(sample.get('lines', []) or [])}"
                    )
                    if sample.get("lines"):
                        print(
                            f"[Warehouse] First line keys: {list(sample['lines'][0].keys()) if isinstance(sample['lines'][0], dict) else 'not a dict'}"
                        )
                orders = [_parse_order(item) for item in response]
                _session_cache = orders
                with contextlib.suppress(Exception):
                    await repository.upsert_replenishments(response, get_db_path())
                return orders
            print(
                f"[Warehouse] GET /warehouse/replenishment: unexpected type {type(response).__name__}"
            )
            return []
        except OfflineError:
            rows = await repository.get_all_replenishments(get_db_path())
            orders = []
            for r in rows:
                lines_data = json.loads(r.get("lines", "[]")) if r.get("lines") else []
                lines = [_parse_line(ln) for ln in lines_data]
                orders.append(
                    WarehouseReplenishment(
                        id=r["id"],
                        status=r.get("status", "PENDING"),
                        note=r.get("note"),
                        createdAt=r.get("created_at", datetime.now()),
                        lines=lines,
                    )
                )
            _session_cache = orders
            return orders
        except Exception as e:
            status = getattr(e, "response", None)
            code = status.status_code if status else "?"
            body = ""
            if status is not None:
                try:
                    body = status.text[:500]
                except Exception:
                    body = "(unreadable)"
            print(f"[Warehouse] GET /warehouse/replenishment failed: HTTP {code}")
            if body:
                print(f"[Warehouse] Response body: {body}")
            if _session_cache:
                print(f"[Warehouse] Returning {len(_session_cache)} cached orders")
                return _session_cache
            if auth_service.is_demo_mode():
                return DEMO_REPLENISHMENTS
            return []

    async def apply_replenishment(self, order_id: int) -> bool:
        global _session_cache
        history = await self.get_replenishment_history()
        order = next((o for o in history if o.id == order_id), None)
        if not order or not order.lines:
            return False
        success = True
        for line in order.lines:
            if line.productId:
                result = await self.update_item_quantity(
                    line.productId, line.quantityDelta
                )
                if result is None:
                    success = False
            if line.rawMaterialId:
                result = await self.update_raw_material(
                    line.rawMaterialId, line.quantityDelta
                )
                if result is None:
                    success = False
        if success:
            for o in _session_cache:
                if o.id == order_id:
                    o.status = "RECEIVED"
                    break
        return success

    def get_all_items_sync(self):
        if auth_service.is_demo_mode():
            return InventoryOverviewResponse(
                products=[
                    InventoryProductRow(
                        productId=1,
                        name="Demo Vodka 500ml",
                        quantity=100,
                        warehouseZone="A1",
                    ),
                    InventoryProductRow(
                        productId=2,
                        name="Demo Whisky 700ml",
                        quantity=50,
                        warehouseZone="B2",
                    ),
                    InventoryProductRow(
                        productId=3,
                        name="Demo Gin 700ml",
                        quantity=30,
                        warehouseZone="A1",
                    ),
                ],
                rawMaterials=[
                    InventoryRawRow(id=1, name="Barley", unit="kg", quantity=500.0),
                    InventoryRawRow(id=2, name="Grapes", unit="kg", quantity=300.0),
                ],
            )
        return None
