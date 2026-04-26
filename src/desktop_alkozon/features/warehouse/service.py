from pydantic import BaseModel
from typing import Optional
from desktop_alkozon.services.api_client import api_client


class WarehouseItem(BaseModel):
    id: int
    name: str
    quantity: int
    unit: str
    price: float
    category: Optional[str] = None
    productId: Optional[int] = None


class WarehouseService:

    async def get_all_items(self) -> list[WarehouseItem]:
        try:
            response = await api_client.get("/inventory")
            if isinstance(response, list):
                return [WarehouseItem(
                    id=item.get("id", 0),
                    name=item.get("product", {}).get("name", f"Produkt {item.get('id')}") if item.get("product") else f"Produkt {item.get('id')}",
                    quantity=item.get("quantity", 0),
                    unit=item.get("product", {}).get("unit", "szt.") if item.get("product") else "szt.",
                    price=item.get("product", {}).get("price", 0.0) if item.get("product") else 0.0,
                    category=item.get("product", {}).get("category") if item.get("product") else None,
                    productId=item.get("productId")
                ) for item in response]
            return []
        except Exception:
            return self.get_all_items_sync()

    async def add_new_item(self, name: str, quantity: int, unit: str, price: float) -> WarehouseItem:
        response = await api_client.post("/warehouse/replenishment", {
            "items": [{"name": name, "quantity": quantity, "unit": unit, "price": price}]
        })
        return WarehouseItem(
            id=0,
            name=name,
            quantity=quantity,
            unit=unit,
            price=price
        )

    async def update_item_quantity(self, item_id: int, delta: int) -> bool:
        try:
            await api_client.patch(f"/inventory/products/{item_id}", {"delta": delta})
            return True
        except Exception:
            return False

    async def get_replenishment_history(self) -> list[dict]:
        try:
            response = await api_client.get("/warehouse/replenishment")
            if isinstance(response, list):
                return response
            return []
        except Exception:
            return []

    def get_all_items_sync(self) -> list[WarehouseItem]:
        return [
            WarehouseItem(id=1, name="Piwo Jasne 0.5l", quantity=1240, unit="szt.", price=4.99, category="Piwo"),
            WarehouseItem(id=2, name="Wodka 0.7l", quantity=450, unit="szt.", price=29.99, category="Wodka"),
            WarehouseItem(id=3, name="Whisky 0.75l", quantity=120, unit="szt.", price=89.99, category="Whisky"),
            WarehouseItem(id=4, name="Coca-Cola 1l", quantity=890, unit="szt.", price=5.49, category="Dodatki"),
        ]

    def add_new_item_sync(self, name: str, quantity: int, unit: str, price: float) -> WarehouseItem:
        return WarehouseItem(id=999, name=name, quantity=quantity, unit=unit, price=price)
