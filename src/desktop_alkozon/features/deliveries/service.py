from pydantic import BaseModel
from typing import Optional
from desktop_alkozon.services.api_client import api_client


class Courier(BaseModel):
    id: int
    name: str
    email: str
    status: str
    vehicle: Optional[str] = None


class Delivery(BaseModel):
    id: int
    courier_name: str
    destination: str
    status: str
    announcement: str
    order_id: Optional[int] = None
    address_snapshot: Optional[str] = None


class DeliveryAnnouncement(BaseModel):
    id: int
    title: str
    content: str
    published_at: Optional[str] = None
    created_by: Optional[int] = None


class DeliveriesService:

    async def get_couriers(self) -> list[Courier]:
        try:
            response = await api_client.get("/admin/users")
            if isinstance(response, list):
                return [Courier(
                    id=item.get("id", 0),
                    name=f"{item.get('firstName', '')} {item.get('lastName', '')}".strip() or item.get("email", ""),
                    email=item.get("email", ""),
                    status="Dostępny" if item.get("isActive", True) else "Nieaktywny",
                    vehicle=None
                ) for item in response if item.get("role") == "EMPLOYEE"]
            return []
        except Exception:
            return self.get_couriers_sync()

    async def get_deliveries(self, status: str | None = None) -> list[Delivery]:
        try:
            params = {"status": status} if status else None
            response = await api_client.get("/deliveries", params)
            if isinstance(response, list):
                return [Delivery(
                    id=item.get("id", 0),
                    courier_name=item.get("courier", {}).get("email", "Nieprzypisany") if item.get("courier") else "Nieprzypisany",
                    destination=item.get("addressSnapshot", ""),
                    status=item.get("status", "PENDING"),
                    announcement="",
                    order_id=item.get("orderId"),
                    address_snapshot=item.get("addressSnapshot")
                ) for item in response]
            return []
        except Exception:
            return self.get_deliveries_sync()

    async def create_announcement(self, title: str, content: str) -> DeliveryAnnouncement:
        response = await api_client.post("/admin/delivery-announcements", {
            "title": title,
            "content": content
        })
        return DeliveryAnnouncement(
            id=response.get("id", 0),
            title=response.get("title", title),
            content=response.get("content", content),
            published_at=response.get("publishedAt"),
            created_by=response.get("createdBy")
        )

    async def get_announcements(self) -> list[DeliveryAnnouncement]:
        try:
            response = await api_client.get("/admin/delivery-announcements")
            if isinstance(response, list):
                return [DeliveryAnnouncement(
                    id=item.get("id", 0),
                    title=item.get("title", ""),
                    content=item.get("content", ""),
                    published_at=item.get("publishedAt"),
                    created_by=item.get("createdBy")
                ) for item in response]
            return []
        except Exception:
            return []

    async def update_delivery_status(self, delivery_id: int, status: str) -> bool:
        try:
            await api_client.patch(f"/deliveries/{delivery_id}/status", {"status": status})
            return True
        except Exception:
            return False

    async def assign_courier(self, delivery_id: int, courier_id: int) -> bool:
        try:
            await api_client.patch(f"/deliveries/{delivery_id}/assign", {"courierId": courier_id})
            return True
        except Exception:
            return False

    def get_couriers_sync(self) -> list[Courier]:
        return [
            Courier(id=1, name="Jan Kowalski", email="jan@example.com", status="Dostępny", vehicle="Fiat Ducato"),
            Courier(id=2, name="Anna Nowak", email="anna@example.com", status="W drodze", vehicle="Mercedes Sprinter"),
            Courier(id=3, name="Piotr Wisniewski", email="piotr@example.com", status="Dostępny", vehicle="VW Transporter"),
        ]

    def get_deliveries_sync(self) -> list[Delivery]:
        return [
            Delivery(id=101, courier_name="Jan Kowalski", destination="Warszawa Centrum", status="W drodze", announcement="Pilna dostawa piwa"),
        ]
