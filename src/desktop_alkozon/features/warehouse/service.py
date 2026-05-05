from desktop_alkozon.core.auth import auth_service
from desktop_alkozon.models.api_models import (
    InventoryOverviewResponse,
    InventoryProductRow,
    InventoryRawRow,
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

    async def add_new_item(self, name: str, quantity: int, unit: str, price: float):
        print("Warehouse replenishment endpoint not yet implemented in API")
        return None

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

    async def get_replenishment_history(self) -> list[dict]:
        print("Warehouse replenishment endpoint not yet implemented in API")
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

    def add_new_item_sync(self, name: str, quantity: int, unit: str, price: float):
        return None
