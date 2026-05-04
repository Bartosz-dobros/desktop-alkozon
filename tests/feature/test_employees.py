import pytest
from desktop_alkozon.features.employees.service import EmployeesService
from desktop_alkozon.features.employees.controller import EmployeesController
from desktop_alkozon.models.api_models import JobOfferResponse, UserAdminResponse, JobOfferStatus


@pytest.fixture
def employees_service():
    return EmployeesService()


@pytest.fixture
def employees_controller():
    return EmployeesController()


def test_get_offers_sync(employees_service):
    offers = employees_service.get_offers_sync()
    
    assert isinstance(offers, list)


def test_get_employees_sync(employees_service):
    employees = employees_service.get_employees_sync()
    
    assert isinstance(employees, list)


def test_job_offer_model():
    offer = JobOfferResponse(
        id=1, title="Kierowca dostaw", description="Test", 
        status=JobOfferStatus.OPEN, createdAt="2024-01-01T00:00:00Z", 
        updatedAt="2024-01-01T00:00:00Z"
    )
    
    assert offer.id == 1
    assert offer.title == "Kierowca dostaw"
    assert offer.status == JobOfferStatus.OPEN


def test_employee_model():
    emp = UserAdminResponse(
        id=101, email="jan@example.com", role="EMPLOYEE", 
        active=True, courier=False
    )
    
    assert emp.id == 101
    assert emp.email == "jan@example.com"
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
        {"id": 1, "title": "Kierowca", "description": "Test", "status": "OPEN", 
         "createdAt": "2024-01-01T00:00:00Z", "updatedAt": "2024-01-01T00:00:00Z"},
        {"id": 2, "title": "Magazynier", "description": "Test 2", "status": "OPEN",
         "createdAt": "2024-01-01T00:00:00Z", "updatedAt": "2024-01-01T00:00:00Z"}
    ]
    mocker.patch("desktop_alkozon.features.employees.service.api_client.get", return_value=mock_response)
    
    offers = await employees_service.get_offers()
    
    assert len(offers) == 2


@pytest.mark.asyncio
async def test_get_employees_async(employees_service, mocker):
    mock_response = [
        {"id": 1, "email": "jan@example.com", "firstName": "Jan", "lastName": "Kowalski", 
         "role": "EMPLOYEE", "active": True, "courier": False}
    ]
    mocker.patch("desktop_alkozon.features.employees.service.api_client.get", return_value=mock_response)
    
    employees = await employees_service.get_employees()
    
    assert len(employees) == 1
