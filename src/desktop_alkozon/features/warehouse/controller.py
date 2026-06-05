from desktop_alkozon.features.warehouse.service import WarehouseService
from desktop_alkozon.models.api_models import (
    InventoryOverviewResponse,
    InventoryProductRow,
    InventoryRawRow,
    WarehouseReplenishment,
)


class WarehouseController:
    def __init__(self):
        self.service = WarehouseService()

    async def get_full_inventory(self) -> InventoryOverviewResponse | None:
        return await self.service.get_all_items()

    async def get_products(self) -> list[InventoryProductRow]:
        result = await self.get_full_inventory()
        if result is None:
            return []
        return result.products

    async def get_raw_materials(self) -> list[InventoryRawRow]:
        result = await self.get_full_inventory()
        if result is None:
            return []
        return result.rawMaterials

    async def order_new_item(
        self,
        product_id: int | None = None,
        quantity_delta: int = 0,
        note: str | None = None,
        raw_material_id: int | None = None,
    ):
        return await self.service.add_new_item(
            product_id, quantity_delta, note, raw_material_id
        )

    async def create_replenishment(
        self, lines: list[dict], note: str | None = None
    ) -> WarehouseReplenishment | None:
        return await self.service.create_replenishment(lines, note)

    async def update_quantity(self, item_id: int, delta: int):
        return await self.service.update_item_quantity(item_id, delta)

    async def get_replenishment_history(self) -> list[WarehouseReplenishment]:
        return await self.service.get_replenishment_history()

    async def mark_received(self, order_id: int) -> bool:
        return await self.service.apply_replenishment(order_id)

    def get_inventory_sync(self) -> InventoryOverviewResponse | None:
        return self.service.get_all_items_sync()

    def get_products_sync(self) -> list[InventoryProductRow]:
        result = self.get_inventory_sync()
        if result is None:
            return []
        if isinstance(result, dict):
            return result.get("products", [])
        return result.products

    def get_raw_materials_sync(self) -> list[InventoryRawRow]:
        result = self.get_inventory_sync()
        if result is None:
            return []
        if isinstance(result, dict):
            return result.get("rawMaterials", [])
        return result.rawMaterials

    async def get_stock_data(self) -> list[InventoryProductRow]:
        return await self.get_products()

    def get_stock_data_sync(self) -> list[InventoryProductRow]:
        return self.get_products_sync()

    def order_new_item_sync(
        self,
        product_id: int | None = None,
        quantity_delta: int = 0,
        note: str | None = None,
        raw_material_id: int | None = None,
    ):
        return None
