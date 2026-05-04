from typing import List, Optional
from desktop_alkozon.services.api_client import api_client
from desktop_alkozon.models.api_models import (
    DeliveryResponse, DeliveryAnnouncementResponse,
    DeliveryAnnouncementRequest, PatchDeliveryStatusRequest,
    PatchDeliveryAssignRequest
)
from desktop_alkozon.core.auth import auth_service


class DeliveriesService:

    async def get_couriers(self) -> List[dict]:
        try:
            response = await api_client.get("/admin/users")
            if isinstance(response, list):
                return [item for item in response
                        if item.get("courier") is True or item.get("role") == "EMPLOYEE"]
            return []
        except Exception:
            if auth_service.is_demo_mode():
                return [
                    {"id": 1, "email": "jan.kowalski@example.com", "active": True, "courier": True},
                    {"id": 2, "email": "anna.nowak@example.com", "active": True, "courier": False}
                ]
            return []

    async def get_deliveries(self, status: str | None = None) -> List[DeliveryResponse]:
        try:
            params = {"status": status} if status else None
            response = await api_client.get("/deliveries", params)
            if isinstance(response, list):
                return [DeliveryResponse(**item) for item in response]
            return []
        except Exception:
            if auth_service.is_demo_mode():
                return [
                    DeliveryResponse(
                        id=101, orderId=1001, courierEmail="jan.kowalski@example.com",
                        status="IN_TRANSIT", addressSnapshot="Warszawa Centrum"
                    )
                ]
            return []

    async def create_announcement(self, title: str, content: str) -> Optional[DeliveryAnnouncementResponse]:
        try:
            response = await api_client.post("/admin/delivery-announcements", {
                "title": title,
                "content": content
            })
            return DeliveryAnnouncementResponse(**response)
        except Exception:
            return None

    async def get_announcements(self) -> List[DeliveryAnnouncementResponse]:
        try:
            response = await api_client.get("/admin/delivery-announcements")
            if isinstance(response, list):
                return [DeliveryAnnouncementResponse(**item) for item in response]
            return []
        except Exception:
            return []

    async def update_delivery_status(self, delivery_id: int, status: str) -> Optional[DeliveryResponse]:
        try:
            response = await api_client.patch(f"/deliveries/{delivery_id}/status", {"status": status})
            return DeliveryResponse(**response)
        except Exception:
            return None

    async def assign_courier(self, delivery_id: int, courier_id: int) -> Optional[DeliveryResponse]:
        try:
            response = await api_client.patch(f"/deliveries/{delivery_id}/assign", {"courierId": courier_id})
            return DeliveryResponse(**response)
        except Exception:
            return None

    def get_couriers_sync(self) -> List[dict]:
        return []

    def get_deliveries_sync(self) -> List[DeliveryResponse]:
        return []

    def get_announcements_sync(self) -> List[DeliveryAnnouncementResponse]:
        return []
