from desktop_alkozon.core.auth import auth_service
from desktop_alkozon.models.api_models import (
    JobOfferResponse,
    JobOfferStatus,
    UserAdminResponse,
)
from desktop_alkozon.services.api_client import api_client


class EmployeesService:
    async def get_offers(self) -> list[JobOfferResponse]:
        try:
            response = await api_client.get("/admin/job-offers")
            if isinstance(response, list):
                return [JobOfferResponse(**item) for item in response]
            return []
        except Exception:
            if auth_service.is_demo_mode():
                return [
                    JobOfferResponse(
                        id=1,
                        title="Kierowca dostaw",
                        description="Praca dla kierowcy",
                        status=JobOfferStatus.OPEN,
                        createdAt="2024-01-01T00:00:00Z",
                        updatedAt="2024-01-01T00:00:00Z",
                    ),
                    JobOfferResponse(
                        id=2,
                        title="Magazynier",
                        description="Praca w magazynie",
                        status=JobOfferStatus.OPEN,
                        createdAt="2024-01-02T00:00:00Z",
                        updatedAt="2024-01-02T00:00:00Z",
                    ),
                ]
            return []

    async def get_employees(self) -> list[UserAdminResponse]:
        try:
            response = await api_client.get("/admin/users")
            if isinstance(response, list):
                return [
                    UserAdminResponse(**item)
                    for item in response
                    if item.get("role") in ["EMPLOYEE", "MANAGER"]
                ]
            return []
        except Exception:
            if auth_service.is_demo_mode():
                return [
                    UserAdminResponse(
                        id=101,
                        email="jan.kowalski@example.com",
                        role="EMPLOYEE",
                        active=True,
                        courier=True,
                    ),
                    UserAdminResponse(
                        id=102,
                        email="anna.nowak@example.com",
                        role="EMPLOYEE",
                        active=True,
                        courier=False,
                    ),
                ]
            return []

    async def post_new_offer(
        self, title: str, description: str
    ) -> JobOfferResponse | None:
        try:
            response = await api_client.post(
                "/admin/job-offers", {"title": title, "description": description}
            )
            return JobOfferResponse(**response)
        except Exception:
            return None

    async def update_offer(
        self, offer_id: int, title: str, description: str, status: str
    ) -> JobOfferResponse | None:
        try:
            if status == "CLOSED":
                response = await api_client.post(f"/admin/job-offers/{offer_id}/close")
            else:
                response = await api_client.put(
                    f"/admin/job-offers/{offer_id}",
                    {"title": title, "description": description},
                )
            return JobOfferResponse(**response)
        except Exception:
            return None

    async def delete_offer(self, offer_id: int) -> bool:
        try:
            await api_client.delete(f"/admin/job-offers/{offer_id}")
            return True
        except Exception:
            return False

    async def hire_employee(self, user_id: int) -> UserAdminResponse | None:
        try:
            response = await api_client.post(f"/admin/users/{user_id}/hire")
            return UserAdminResponse(**response)
        except Exception:
            return None

    async def terminate_employee(self, user_id: int) -> UserAdminResponse | None:
        try:
            response = await api_client.post(f"/admin/users/{user_id}/terminate")
            return UserAdminResponse(**response)
        except Exception:
            return None

    def get_offers_sync(self) -> list[JobOfferResponse]:
        return []

    def get_employees_sync(self) -> list[UserAdminResponse]:
        return []
