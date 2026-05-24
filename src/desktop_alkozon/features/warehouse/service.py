import json

from desktop_alkozon.core.auth import auth_service
from desktop_alkozon.models.api_models import (
    InventoryOverviewResponse,
    InventoryProductRow,
    InventoryRawRow,
    WarehouseReplenishment,
)
from desktop_alkozon.services.api_client import api_client


class WarehouseService:
    async def get_all_items(self) -> InventoryOverviewResponse | None:
        try:
            response = await api_client.get("/inventory")
            return InventoryOverviewResponse(**response)
        except Exception:
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
                    ],
                    rawMaterials=[
                        InventoryRawRow(id=1, name="Barley", unit="kg", quantity=500.0)
                    ],
                )
            return None

    async def add_new_item(
        self, product_id: int, quantity_delta: int, note: str | None = None
    ) -> WarehouseReplenishment | None:
        try:
            payload = {
                "lines": [{"productId": product_id, "quantityDelta": quantity_delta}],
            }
            if note:
                payload["note"] = note

            response = await api_client.post("/warehouse/replenishment", payload)
            return WarehouseReplenishment(**response)
        except Exception as e:
            error_text = str(e)
            if "Extra data" in error_text and "201" in error_text:
                try:
                    raw_response = e.response.text
                    first_brace = raw_response.find("{")
                    last_brace = self._find_matching_brace(raw_response, first_brace)
                    if last_brace > 0:
                        valid_json = raw_response[first_brace : last_brace + 1]
                        data = json.loads(valid_json)
                        return WarehouseReplenishment(**data)
                except Exception:
                    pass
            return None

    def _find_matching_brace(self, text: str, start: int) -> int:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    return i
        return -1

    async def update_item_quantity(
        self, item_id: int, delta: int
    ) -> InventoryProductRow | None:
        try:
            response = await api_client.patch(
                f"/inventory/products/{item_id}", {"delta": delta}
            )
            return InventoryProductRow(**response)
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
        except Exception:
            return None

    async def get_replenishment_history(self) -> list[WarehouseReplenishment]:
        try:
            response = await api_client.get("/warehouse/replenishment")
            if isinstance(response, list):
                return [WarehouseReplenishment(**item) for item in response]
            return []
        except Exception:
            return []

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
                ],
                rawMaterials=[
                    InventoryRawRow(id=1, name="Barley", unit="kg", quantity=500.0)
                ],
            )
        return None

    def add_new_item_sync(
        self, product_id: int, quantity_delta: int, note: str | None = None
    ):
        return None
