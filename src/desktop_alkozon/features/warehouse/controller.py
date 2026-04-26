from desktop_alkozon.features.warehouse.service import WarehouseService


class WarehouseController:

    def __init__(self):
        self.service = WarehouseService()

    async def get_stock_data(self):
        return await self.service.get_all_items()

    async def order_new_item(self, name: str, quantity: int, unit: str, price: float):
        return await self.service.add_new_item(name, quantity, unit, price)

    async def update_quantity(self, item_id: int, delta: int):
        return await self.service.update_item_quantity(item_id, delta)

    async def get_replenishment_history(self):
        return await self.service.get_replenishment_history()

    def get_stock_data_sync(self):
        return self.service.get_all_items_sync()

    def order_new_item_sync(self, name: str, quantity: int, unit: str, price: float):
        return self.service.add_new_item_sync(name, quantity, unit, price)
