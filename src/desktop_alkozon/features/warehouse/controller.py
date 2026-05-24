from desktop_alkozon.features.warehouse.service import WarehouseService
from desktop_alkozon.models.api_models import InventoryProductRow


class WarehouseController:
    def __init__(self):
        self.service = WarehouseService()

    async def get_stock_data(self) -> list[InventoryProductRow]:
        result = await self.service.get_all_items()
        if result is None:
            return []
        if isinstance(result, dict):
            return result.get("products", [])
        return result.products

    async def order_new_item(
        self, product_id: int, quantity_delta: int, note: str | None = None
    ):
        return await self.service.add_new_item(product_id, quantity_delta, note)

    async def update_quantity(self, item_id: int, delta: int):
        return await self.service.update_item_quantity(item_id, delta)

    async def get_replenishment_history(self):
        return await self.service.get_replenishment_history()

    def get_stock_data_sync(self) -> list[InventoryProductRow]:
        result = self.service.get_all_items_sync()
        if result is None:
            return []
        if isinstance(result, dict):
            return result.get("products", [])
        return result.products

    def order_new_item_sync(
        self, product_id: int, quantity_delta: int, note: str | None = None
    ):
        return None
