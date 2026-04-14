import pytest
from desktop_alkozon.features.employees.service import EmployeesService, JobOffer, Employee
from desktop_alkozon.features.employees.controller import EmployeesController


@pytest.fixture
def employees_service():
    return EmployeesService()


@pytest.fixture
def employees_controller():
    return EmployeesController()


def test_get_offers(employees_service):
    offers = employees_service.get_offers()
    
    assert len(offers) == 2
    assert all(isinstance(o, JobOffer) for o in offers)


def test_get_employees(employees_service):
    employees = employees_service.get_employees()
    
    assert len(employees) == 1
    assert all(isinstance(e, Employee) for e in employees)


def test_post_new_offer(employees_service):
    new_offer = employees_service.post_new_offer("Test Job", 5000.0)
    
    assert new_offer.title == "Test Job"
    assert new_offer.salary == 5000.0
    assert new_offer.status == "Otwarta"
    assert len(employees_service.get_offers()) == 3


def test_hire_employee(employees_service, capsys):
    employees_service.hire_employee(1, "Test Employee")
    
    captured = capsys.readouterr()
    assert "Zatrudniono" in captured.out


def test_fire_employee(employees_service, capsys):
    employees_service.fire_employee(101)
    
    captured = capsys.readouterr()
    assert "Zwolniono" in captured.out


def test_controller_get_offers(employees_controller):
    offers = employees_controller.get_offers()
    
    assert len(offers) == 2


def test_controller_get_employees(employees_controller):
    employees = employees_controller.get_employees()
    
    assert len(employees) == 1


def test_controller_create_offer(employees_controller):
    offer = employees_controller.create_offer("New Position", 6000.0)
    
    assert offer.title == "New Position"
    assert offer.salary == 6000.0
