from pydantic import BaseModel
from typing import List

class JobOffer(BaseModel):
    id: int
    title: str
    salary: float
    status: str

class Employee(BaseModel):
    id: int
    name: str
    position: str
    status: str

class EmployeesService:
    def __init__(self):
        self.offers = [
            JobOffer(id=1, title="Kierowca dostaw", salary=4500.0, status="Otwarta"),
            JobOffer(id=2, title="Magazynier", salary=3800.0, status="Otwarta"),
        ]
        self.employees = [
            Employee(id=101, name="Jan Kowalski", position="Kierowca", status="Zatrudniony"),
        ]

    def get_offers(self) -> List[JobOffer]:
        return self.offers

    def get_employees(self) -> List[Employee]:
        return self.employees

    def post_new_offer(self, title: str, salary: float) -> JobOffer:
        new_id = max(o.id for o in self.offers) + 1
        new_offer = JobOffer(id=new_id, title=title, salary=salary, status="Otwarta")
        self.offers.append(new_offer)
        return new_offer

    def hire_employee(self, offer_id: int, name: str):
        print(f"Zatrudniono: {name} na ofertę {offer_id}")

    def fire_employee(self, employee_id: int):
        print(f"Zwolniono pracownika ID {employee_id}")