import jwt

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

    async def get_all_users(self) -> list[UserAdminResponse]:
        try:
            response = await api_client.get("/admin/users")
            if isinstance(response, list):
                return [UserAdminResponse(**item) for item in response]
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
        self, title: str, description: str, salary: float | None = None
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

    async def update_user(
        self, user_id: int, role: str, active: bool, courier: bool
    ) -> UserAdminResponse | None:
        try:
            response = await api_client.put(
                f"/admin/users/{user_id}",
                {"role": role, "active": active, "courier": courier},
            )
            return UserAdminResponse(**response)
        except Exception:
            return None

    async def create_employee_account(
        self,
        email: str,
        password: str,
        first_name: str = "",
        last_name: str = "",
        courier: bool = False,
        role: str = "EMPLOYEE",
    ) -> UserAdminResponse | None:
        try:
            register_data = {
                "email": email,
                "password": password,
                "firstName": first_name,
                "lastName": last_name,
                "ageConfirmed": True,
                "adultConfirmed": True,
            }
            register_response = await api_client.post("/auth/register", register_data)
            if not register_response:
                return None

            access_token = register_response.get("accessToken", "")
            if not access_token:
                return None

            claims = jwt.decode(access_token, options={"verify_signature": False})
            user_id = int(claims.get("sub", 0))
            if not user_id:
                return None

            update_response = await api_client.put(
                f"/admin/users/{user_id}",
                {
                    "role": role,
                    "active": True,
                    "courier": courier,
                },
            )
            return UserAdminResponse(**update_response) if update_response else None
        except Exception as e:
            print(f"Error creating employee account: {e}")
            return None

    def get_offers_sync(self) -> list[JobOfferResponse]:
        return []

    def get_employees_sync(self) -> list[UserAdminResponse]:
        return []
