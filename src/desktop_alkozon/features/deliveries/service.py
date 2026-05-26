from desktop_alkozon.core.auth import auth_service
from desktop_alkozon.models.api_models import (
    DeliveryAnnouncementResponse,
    DeliveryResponse,
)
from desktop_alkozon.services.api_client import api_client


class DeliveriesService:
    async def get_couriers(self) -> list[dict]:
        try:
            response = await api_client.get("/admin/users")
            if isinstance(response, list):
                return [
                    item
                    for item in response
                    if item.get("courier") is True or item.get("role") == "EMPLOYEE"
                ]
            return []
        except Exception:
            if auth_service.is_demo_mode():
                return [
                    {
                        "id": 1,
                        "email": "jan.kowalski@example.com",
                        "active": True,
                        "courier": True,
                    },
                    {
                        "id": 2,
                        "email": "anna.nowak@example.com",
                        "active": True,
                        "courier": True,
                    },
                    {
                        "id": 3,
                        "email": "piotr.zielinski@example.com",
                        "active": True,
                        "courier": False,
                    },
                ]
            return []

    async def get_unassigned_couriers(self) -> list[dict]:
        try:
            couriers = await self.get_couriers()
            deliveries = await self.get_deliveries()
            assigned_ids = {d.courierId for d in deliveries if d.courierId is not None}
            return [c for c in couriers if c.get("id") not in assigned_ids]
        except Exception:
            if auth_service.is_demo_mode():
                return [
                    {
                        "id": 2,
                        "email": "anna.nowak@example.com",
                        "active": True,
                        "courier": True,
                    },
                ]
            return []

    async def get_deliveries(self, status: str | None = None) -> list[DeliveryResponse]:
        try:
            response = await api_client.get("/deliveries")
            if isinstance(response, list):
                items = [DeliveryResponse(**item) for item in response]
                if status:
                    return [d for d in items if d.status.value == status]
                return items
            return []
        except Exception:
            if auth_service.is_demo_mode():
                return [
                    DeliveryResponse(
                        id=101,
                        orderId=1001,
                        courierId=1,
                        courierEmail="jan.kowalski@example.com",
                        status="PENDING",
                        addressSnapshot="Warszawa Centrum",
                    ),
                    DeliveryResponse(
                        id=102,
                        orderId=1002,
                        courierId=None,
                        courierEmail=None,
                        status="PENDING",
                        addressSnapshot="Krakow Rynek",
                    ),
                ]
            return []

    async def create_announcement(
        self, title: str, content: str
    ) -> DeliveryAnnouncementResponse | None:
        try:
            response = await api_client.post(
                "/admin/delivery-announcements", {"title": title, "content": content}
            )
            return DeliveryAnnouncementResponse(**response)
        except Exception:
            return None

    async def get_announcements(self) -> list[DeliveryAnnouncementResponse]:
        try:
            response = await api_client.get("/admin/delivery-announcements")
            if isinstance(response, list):
                return [DeliveryAnnouncementResponse(**item) for item in response]
            return []
        except Exception:
            return []

    async def update_delivery_status(
        self, delivery_id: int, status: str
    ) -> DeliveryResponse | None:
        try:
            response = await api_client.patch(
                f"/deliveries/{delivery_id}/status", {"status": status}
            )
            return DeliveryResponse(**response)
        except Exception:
            return None

    async def assign_courier(
        self, delivery_id: int, courier_id: int
    ) -> DeliveryResponse | None:
        try:
            response = await api_client.patch(
                f"/deliveries/{delivery_id}/assign", {"courierId": courier_id}
            )
            return DeliveryResponse(**response)
        except Exception:
            return None

    def get_couriers_sync(self) -> list[dict]:
        return []

    def get_unassigned_couriers_sync(self) -> list[dict]:
        return []

    def get_deliveries_sync(self) -> list[DeliveryResponse]:
        return []
