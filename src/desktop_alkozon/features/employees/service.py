import contextlib
from datetime import datetime

import jwt

from desktop_alkozon.core import repository
from desktop_alkozon.core.auth import auth_service
from desktop_alkozon.core.database import get_db_path
from desktop_alkozon.core.exceptions import OfflineError
from desktop_alkozon.core.outbox import enqueue
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
                items = [JobOfferResponse(**item) for item in response]
                with contextlib.suppress(Exception):
                    await repository.upsert_job_offers(response, get_db_path())
                return items
            return []
        except OfflineError:
            db_path = get_db_path()
            rows = await repository.get_all_job_offers(db_path)
            return [
                JobOfferResponse(
                    id=r["id"],
                    title=r["title"],
                    description=r.get("description"),
                    status=r.get("status", "OPEN"),
                    createdAt=r.get("created_at") or datetime.now(),
                    updatedAt=r.get("updated_at") or datetime.now(),
                )
                for r in rows
            ]
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
                with contextlib.suppress(Exception):
                    await repository.upsert_users(response, get_db_path())
                return [
                    UserAdminResponse(**item)
                    for item in response
                    if item.get("role") in ["EMPLOYEE", "MANAGER"]
                ]
            return []
        except OfflineError:
            rows = await repository.get_all_users(get_db_path())
            return [
                UserAdminResponse(
                    **{
                        "id": r["id"],
                        "email": r["email"],
                        "role": r["role"],
                        "active": bool(r["active"]),
                        "courier": bool(r["courier"]),
                        "ageConfirmedAt": r.get("age_confirmed_at"),
                    }
                )
                for r in rows
                if r.get("role") in ("EMPLOYEE", "MANAGER")
            ]
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
                with contextlib.suppress(Exception):
                    await repository.upsert_users(response, get_db_path())
                return [UserAdminResponse(**item) for item in response]
            return []
        except OfflineError:
            rows = await repository.get_all_users(get_db_path())
            return [
                UserAdminResponse(
                    **{
                        "id": r["id"],
                        "email": r["email"],
                        "role": r["role"],
                        "active": bool(r["active"]),
                        "courier": bool(r["courier"]),
                        "ageConfirmedAt": r.get("age_confirmed_at"),
                    }
                )
                for r in rows
            ]
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
            if response:
                with contextlib.suppress(Exception):
                    await repository.upsert_job_offers([response], get_db_path())
            return JobOfferResponse(**response) if response else None
        except OfflineError:
            db_path = get_db_path()
            await enqueue(
                "job_offer",
                "POST",
                "/admin/job-offers",
                request_body={"title": title, "description": description},
                db_path=db_path,
            )
            return None
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
            if response:
                with contextlib.suppress(Exception):
                    await repository.upsert_job_offers([response], get_db_path())
            return JobOfferResponse(**response) if response else None
        except OfflineError:
            db_path = get_db_path()
            endpoint = (
                f"/admin/job-offers/{offer_id}/close"
                if status == "CLOSED"
                else f"/admin/job-offers/{offer_id}"
            )
            method = "POST" if status == "CLOSED" else "PUT"
            body = (
                None
                if status == "CLOSED"
                else {"title": title, "description": description}
            )
            await enqueue(
                "job_offer",
                method,
                endpoint,
                entity_id=str(offer_id),
                request_body=body,
                db_path=db_path,
            )
            return None
        except Exception:
            return None

    async def delete_offer(self, offer_id: int) -> bool:
        try:
            await api_client.delete(f"/admin/job-offers/{offer_id}")
            return True
        except OfflineError:
            await enqueue(
                "job_offer",
                "DELETE",
                f"/admin/job-offers/{offer_id}",
                entity_id=str(offer_id),
                db_path=get_db_path(),
            )
            return False
        except Exception:
            return False

    async def hire_employee(self, user_id: int) -> UserAdminResponse | None:
        try:
            response = await api_client.post(f"/admin/users/{user_id}/hire")
            if response:
                with contextlib.suppress(Exception):
                    await repository.upsert_users([response], get_db_path())
            return UserAdminResponse(**response) if response else None
        except OfflineError:
            await enqueue(
                "user",
                "POST",
                f"/admin/users/{user_id}/hire",
                entity_id=str(user_id),
                db_path=get_db_path(),
            )
            return None
        except Exception:
            return None

    async def terminate_employee(self, user_id: int) -> UserAdminResponse | None:
        try:
            response = await api_client.post(f"/admin/users/{user_id}/terminate")
            if response:
                with contextlib.suppress(Exception):
                    await repository.upsert_users([response], get_db_path())
            return UserAdminResponse(**response) if response else None
        except OfflineError:
            await enqueue(
                "user",
                "POST",
                f"/admin/users/{user_id}/terminate",
                entity_id=str(user_id),
                db_path=get_db_path(),
            )
            return None
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
            if response:
                with contextlib.suppress(Exception):
                    await repository.upsert_users([response], get_db_path())
            return UserAdminResponse(**response) if response else None
        except OfflineError:
            await enqueue(
                "user",
                "PUT",
                f"/admin/users/{user_id}",
                entity_id=str(user_id),
                request_body={"role": role, "active": active, "courier": courier},
                db_path=get_db_path(),
            )
            return None
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
            if hasattr(e, "response") and hasattr(e.response, "text"):
                print(f"Error creating employee account: {e}, body: {e.response.text}")
            else:
                print(f"Error creating employee account: {e}")
            return None

    def get_offers_sync(self) -> list[JobOfferResponse]:
        return []

    def get_employees_sync(self) -> list[UserAdminResponse]:
        return []
