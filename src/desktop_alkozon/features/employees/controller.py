from desktop_alkozon.features.employees.service import EmployeesService


class EmployeesController:
    def __init__(self):
        self.service = EmployeesService()

    async def get_offers(self):
        return await self.service.get_offers()

    async def get_employees(self):
        return await self.service.get_employees()

    async def create_offer(self, title: str, description: str, salary: float | None = None):
        return await self.service.post_new_offer(title, description, salary)

    async def update_offer(self, offer_id: int, title: str, description: str, status: str):
        return await self.service.update_offer(offer_id, title, description, status)

    async def delete_offer(self, offer_id: int):
        return await self.service.delete_offer(offer_id)

    async def hire(self, user_id: int):
        return await self.service.hire_employee(user_id)

    async def terminate(self, user_id: int):
        return await self.service.terminate_employee(user_id)

    def get_offers_sync(self):
        return self.service.get_offers_sync()

    def get_employees_sync(self):
        return self.service.get_employees_sync()
