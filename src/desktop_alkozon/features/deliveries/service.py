import contextlib
import json

from desktop_alkozon.core import repository
from desktop_alkozon.core.auth import auth_service
from desktop_alkozon.core.database import get_db_path
from desktop_alkozon.core.exceptions import OfflineError
from desktop_alkozon.core.outbox import enqueue
from desktop_alkozon.models.api_models import (
    DeliveryAnnouncementResponse,
    DeliveryDetails,
    DeliveryResponse,
)
from desktop_alkozon.services.api_client import api_client


class DeliveriesService:
    async def get_couriers(self) -> list[dict]:
        try:
            response = await api_client.get("/admin/users")
            if isinstance(response, list):
                with contextlib.suppress(Exception):
                    await repository.upsert_users(response, get_db_path())
                return [
                    item
                    for item in response
                    if item.get("courier") is True or item.get("role") == "EMPLOYEE"
                ]
            return []
        except OfflineError:
            rows = await repository.get_all_users(get_db_path())
            return [
                {
                    "id": r["id"],
                    "email": r["email"],
                    "active": bool(r["active"]),
                    "courier": bool(r["courier"]),
                    "role": r["role"],
                }
                for r in rows
                if r.get("courier") or r.get("role") in ("EMPLOYEE",)
            ]
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
            print(
                f"[DEBUG] API /deliveries response type={type(response).__name__}",
                flush=True,
            )
            if isinstance(response, list):
                print(f"[DEBUG] API returned {len(response)} deliveries", flush=True)
                if response:
                    print(
                        f"[DEBUG] First item keys: {list(response[0].keys())}",
                        flush=True,
                    )
                with contextlib.suppress(Exception):
                    await repository.upsert_deliveries(response, get_db_path())
                items = []
                for i, item in enumerate(response):
                    try:
                        items.append(DeliveryResponse(**item))
                    except Exception as e:
                        print(f"[DEBUG] Skipping item {i}: {e}", flush=True)
                print(
                    f"[DEBUG] Parsed {len(items)}/{len(response)} deliveries",
                    flush=True,
                )
                if status:
                    filtered = [d for d in items if d.status.value == status]
                    print(
                        f"[DEBUG] Filtered to {len(filtered)} with status={status}",
                        flush=True,
                    )
                    return filtered
                return items
            print(f"[DEBUG] Response is not a list: {response}", flush=True)
            return []
        except OfflineError:
            rows = await repository.get_all_deliveries(get_db_path())
            items = []
            for r in rows:
                items.append(
                    DeliveryResponse(
                        id=r["id"],
                        orderId=r.get("order_id") or 0,
                        courierId=r.get("courier_id"),
                        courierEmail=r.get("courier_email"),
                        status=r.get("status", "PENDING"),
                        deliveryDetails=json.loads(r.get("delivery_details") or "{}"),
                        customerEmail=r.get("customer_email"),
                        startedAt=r.get("started_at"),
                        deliveredAt=r.get("delivered_at"),
                    )
                )
            if status:
                return [d for d in items if d.status.value == status]
            return items
        except Exception:
            print("[DEBUG] Unexpected error in get_deliveries", flush=True)
            import traceback

            traceback.print_exc()
            if auth_service.is_demo_mode():
                return [
                    DeliveryResponse(
                        id=101,
                        orderId=1001,
                        courierId=1,
                        courierEmail="jan.kowalski@example.com",
                        status="PENDING",
                        deliveryDetails=DeliveryDetails(
                            recipientName="Jan Kowalski",
                            streetAddress="Marszalkowska 1",
                            city="Warszawa",
                            postalCode="00-001",
                            country="Polska",
                        ),
                    ),
                    DeliveryResponse(
                        id=102,
                        orderId=1002,
                        courierId=None,
                        courierEmail=None,
                        status="PENDING",
                        deliveryDetails=DeliveryDetails(
                            recipientName="Anna Nowak",
                            streetAddress="Florianska 15",
                            city="Krakow",
                            postalCode="31-021",
                            country="Polska",
                        ),
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
        except OfflineError:
            await enqueue(
                "announcement",
                "POST",
                "/admin/delivery-announcements",
                request_body={"title": title, "content": content},
                db_path=get_db_path(),
            )
            return None
        except Exception:
            return None

    async def get_announcements(self) -> list[DeliveryAnnouncementResponse]:
        try:
            response = await api_client.get("/admin/delivery-announcements")
            if isinstance(response, list):
                with contextlib.suppress(Exception):
                    await repository.upsert_announcements(response, get_db_path())
                return [DeliveryAnnouncementResponse(**item) for item in response]
            return []
        except OfflineError:
            rows = await repository.get_all_announcements(get_db_path())
            return [
                DeliveryAnnouncementResponse(
                    id=r["id"],
                    title=r["title"],
                    content=r["content"],
                    createdBy=r.get("created_by"),
                    createdAt=r.get("created_at"),
                )
                for r in rows
            ]
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
        except OfflineError:
            await enqueue(
                "delivery",
                "PATCH",
                f"/deliveries/{delivery_id}/status",
                entity_id=str(delivery_id),
                request_body={"status": status},
                db_path=get_db_path(),
            )
            return None
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
        except OfflineError:
            await enqueue(
                "delivery",
                "PATCH",
                f"/deliveries/{delivery_id}/assign",
                entity_id=str(delivery_id),
                request_body={"courierId": courier_id},
                db_path=get_db_path(),
            )
            return None
        except Exception:
            return None

    def get_couriers_sync(self) -> list[dict]:
        return []

    def get_unassigned_couriers_sync(self) -> list[dict]:
        return []

    def get_deliveries_sync(self) -> list[DeliveryResponse]:
        return []
