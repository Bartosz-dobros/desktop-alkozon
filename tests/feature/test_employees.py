import pytest
from desktop_alkozon.features.employees.service import EmployeesService, JobOffer, Employee
from desktop_alkozon.features.employees.controller import EmployeesController


@pytest.fixture
def employees_service():
    return EmployeesService()


@pytest.fixture
def employees_controller():
    return EmployeesController()


def test_get_offers_sync(employees_service):
    offers = employees_service.get_offers_sync()
    
    assert len(offers) == 2
    assert all(isinstance(o, JobOffer) for o in offers)


def test_get_employees_sync(employees_service):
    employees = employees_service.get_employees_sync()
    
    assert len(employees) == 1
    assert all(isinstance(e, Employee) for e in employees)


def test_job_offer_model():
    offer = JobOffer(id=1, title="Kierowca dostaw", description="Test", salary=4500.0, status="Otwarta")
    
    assert offer.id == 1
    assert offer.title == "Kierowca dostaw"
    assert offer.salary == 4500.0
    assert offer.status == "Otwarta"


def test_employee_model():
    emp = Employee(id=101, name="Jan Kowalski", email="jan@example.com", position="Kierowca", role="EMPLOYEE", status="Aktywny")
    
    assert emp.id == 101
    assert emp.name == "Jan Kowalski"
    assert emp.role == "EMPLOYEE"


def test_controller_get_offers(employees_controller):
    offers = employees_controller.get_offers_sync()
    
    assert isinstance(offers, list)


def test_controller_get_employees(employees_controller):
    employees = employees_controller.get_employees_sync()
    
    assert isinstance(employees, list)


@pytest.mark.asyncio
async def test_get_offers_async(employees_service, mocker):
    mock_response = [
        {"id": 1, "title": "Kierowca", "description": "Test", "status": "OPEN"},
        {"id": 2, "title": "Magazynier", "description": "Test 2", "status": "OPEN"}
    ]
    mocker.patch("desktop_alkozon.features.employees.service.api_client.get", return_value=mock_response)
    
    offers = await employees_service.get_offers()
    
    assert len(offers) == 2


@pytest.mark.asyncio
async def test_get_employees_async(employees_service, mocker):
    mock_response = [
        {"id": 1, "email": "jan@example.com", "firstName": "Jan", "lastName": "Kowalski", "role": "EMPLOYEE", "isActive": True},
    ]
    mocker.patch("desktop_alkozon.features.employees.service.api_client.get", return_value=mock_response)
    
    employees = await employees_service.get_employees()
    
    assert len(employees) == 1
