from desktop_alkozon.features.employees.service import EmployeesService

class EmployeesController:
    def __init__(self):
        self.service = EmployeesService()

    def get_offers(self):
        return self.service.get_offers()

    def get_employees(self):
        return self.service.get_employees()

    def create_offer(self, title: str, salary: float):
        return self.service.post_new_offer(title, salary)

    def hire(self, offer_id: int, name: str):
        self.service.hire_employee(offer_id, name)

    def fire(self, employee_id: int):
        self.service.fire_employee(employee_id)