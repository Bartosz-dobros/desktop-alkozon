from pydantic import BaseModel
from typing import List

class WarehouseItem(BaseModel):
    id: int
    name: str
    quantity: int
    unit: str
    price: float

class WarehouseService:

    def __init__(self):
        self._mock_items: List[WarehouseItem] = [
            WarehouseItem(id=1, name="Piwo Jasne 0.5l", quantity=1240, unit="szt.", price=4.99),
            WarehouseItem(id=2, name="Wódka 0.7l", quantity=450, unit="szt.", price=29.99),
            WarehouseItem(id=3, name="Whisky 0.75l", quantity=120, unit="szt.", price=89.99),
            WarehouseItem(id=4, name="Coca-Cola 1l", quantity=890, unit="szt.", price=5.49),
        ]

    def get_all_items(self) -> List[WarehouseItem]:
        return self._mock_items

    def add_new_item(self, name: str, quantity: int, unit: str, price: float) -> WarehouseItem:
        new_id = max(item.id for item in self._mock_items) + 1
        new_item = WarehouseItem(id=new_id, name=name, quantity=quantity, unit=unit, price=price)
        self._mock_items.append(new_item)
        return new_item