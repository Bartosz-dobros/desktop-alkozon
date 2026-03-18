from desktop_alkozon.features.warehouse.service import WarehouseService

class WarehouseController:

    def __init__(self):
        self.service = WarehouseService()

    def get_stock_data(self):
        return self.service.get_all_items()

    def order_new_item(self, name: str, quantity: int, unit: str, price: float):
        return self.service.add_new_item(name, quantity, unit, price)