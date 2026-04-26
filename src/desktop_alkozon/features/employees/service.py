from pydantic import BaseModel
from typing import Optional
from desktop_alkozon.services.api_client import api_client
from desktop_alkozon.models.api_models import JobOffer as ApiJobOffer, User, JobOfferStatus


class JobOffer(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    salary: Optional[float] = None
    status: str


class Employee(BaseModel):
    id: int
    name: str
    email: str
    position: str
    role: str
    status: str


class EmployeesService:

    async def get_offers(self) -> list[JobOffer]:
        try:
            response = await api_client.get("/admin/job-offers")
            if isinstance(response, list):
                return [JobOffer(
                    id=item.get("id", 0),
                    title=item.get("title", ""),
                    description=item.get("description"),
                    salary=None,
                    status=item.get("status", "OPEN")
                ) for item in response]
            return []
        except Exception:
            return []

    async def get_employees(self) -> list[Employee]:
        try:
            response = await api_client.get("/admin/users")
            if isinstance(response, list):
                return [Employee(
                    id=item.get("id", 0),
                    name=f"{item.get('firstName', '')} {item.get('lastName', '')}".strip() or item.get("email", ""),
                    email=item.get("email", ""),
                    position=item.get("role", ""),
                    role=item.get("role", ""),
                    status="Aktywny" if item.get("isActive", True) else "Nieaktywny"
                ) for item in response if item.get("role") in ["EMPLOYEE", "MANAGER"]]
            return []
        except Exception:
            return []

    async def post_new_offer(self, title: str, description: str, salary: float | None = None) -> JobOffer:
        response = await api_client.post("/admin/job-offers", {
            "title": title,
            "description": description,
            "status": "OPEN"
        })
        return JobOffer(
            id=response.get("id", 0),
            title=response.get("title", title),
            description=response.get("description"),
            salary=salary,
            status=response.get("status", "OPEN")
        )

    async def update_offer(self, offer_id: int, title: str, description: str, status: str) -> JobOffer:
        response = await api_client.put(f"/admin/job-offers/{offer_id}", {
            "title": title,
            "description": description,
            "status": status
        })
        return JobOffer(
            id=response.get("id", 0),
            title=response.get("title", ""),
            description=response.get("description"),
            salary=None,
            status=response.get("status", "OPEN")
        )

    async def delete_offer(self, offer_id: int) -> bool:
        try:
            await api_client.delete(f"/admin/job-offers/{offer_id}")
            return True
        except Exception:
            return False

    async def hire_employee(self, user_id: int) -> bool:
        try:
            await api_client.post(f"/admin/users/{user_id}/hire")
            return True
        except Exception:
            return False

    async def terminate_employee(self, user_id: int) -> bool:
        try:
            await api_client.post(f"/admin/users/{user_id}/terminate")
            return True
        except Exception:
            return False

    def get_offers_sync(self) -> list[JobOffer]:
        return [
            JobOffer(id=1, title="Kierowca dostaw", description="Praca dla kierowcy", salary=4500.0, status="Otwarta"),
            JobOffer(id=2, title="Magazynier", description="Praca w magazynie", salary=3800.0, status="Otwarta"),
        ]

    def get_employees_sync(self) -> list[Employee]:
        return [
            Employee(id=101, name="Jan Kowalski", email="jan@example.com", position="Kierowca", role="EMPLOYEE", status="Aktywny"),
        ]
