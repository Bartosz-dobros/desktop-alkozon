import pytest

from desktop_alkozon.features.employees.controller import EmployeesController
from desktop_alkozon.features.employees.service import EmployeesService
from desktop_alkozon.models.api_models import (
    JobOfferResponse,
    JobOfferStatus,
    UserAdminResponse,
)


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
        id=1,
        title="Kierowca dostaw",
        description="Test",
        status=JobOfferStatus.OPEN,
        createdAt="2024-01-01T00:00:00Z",
        updatedAt="2024-01-01T00:00:00Z",
    )

    assert offer.id == 1
    assert offer.title == "Kierowca dostaw"
    assert offer.status == JobOfferStatus.OPEN


def test_employee_model():
    emp = UserAdminResponse(
        id=101, email="jan@example.com", role="EMPLOYEE", active=True, courier=False
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
        {
            "id": 1,
            "title": "Kierowca",
            "description": "Test",
            "status": "OPEN",
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-01T00:00:00Z",
        },
        {
            "id": 2,
            "title": "Magazynier",
            "description": "Test 2",
            "status": "OPEN",
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-01T00:00:00Z",
        },
    ]
    mocker.patch(
        "desktop_alkozon.features.employees.service.api_client.get",
        return_value=mock_response,
    )

    offers = await employees_service.get_offers()

    assert len(offers) == 2


@pytest.mark.asyncio
async def test_get_employees_async(employees_service, mocker):
    mock_response = [
        {
            "id": 1,
            "email": "jan@example.com",
            "firstName": "Jan",
            "lastName": "Kowalski",
            "role": "EMPLOYEE",
            "active": True,
            "courier": False,
        }
    ]
    mocker.patch(
        "desktop_alkozon.features.employees.service.api_client.get",
        return_value=mock_response,
    )

    employees = await employees_service.get_employees()

    assert len(employees) == 1


@pytest.mark.asyncio
async def test_get_all_users(employees_service, mocker):
    mock_response = [
        {
            "id": 1,
            "email": "jan@example.com",
            "role": "EMPLOYEE",
            "active": True,
            "courier": False,
        },
        {
            "id": 2,
            "email": "customer@example.com",
            "role": "CUSTOMER",
            "active": True,
            "courier": False,
        },
    ]
    mocker.patch(
        "desktop_alkozon.features.employees.service.api_client.get",
        return_value=mock_response,
    )

    users = await employees_service.get_all_users()

    assert len(users) == 2


@pytest.mark.asyncio
async def test_update_user(employees_service, mocker):
    mock_response = {
        "id": 1,
        "email": "jan@example.com",
        "role": "MANAGER",
        "active": True,
        "courier": True,
    }
    mock_put = mocker.patch(
        "desktop_alkozon.features.employees.service.api_client.put",
        return_value=mock_response,
    )

    result = await employees_service.update_user(1, "MANAGER", True, True)

    assert result is not None
    assert result.role == "MANAGER"
    assert result.courier is True
    mock_put.assert_called_once_with(
        "/admin/users/1",
        {"role": "MANAGER", "active": True, "courier": True},
    )


@pytest.mark.asyncio
async def test_create_employee_account_full_flow(employees_service, mocker):
    import base64
    import json

    header = (
        base64.urlsafe_b64encode(json.dumps({"alg": "HS256"}).encode())
        .rstrip(b"=")
        .decode()
    )
    payload = (
        base64.urlsafe_b64encode(
            json.dumps(
                {"sub": 123, "email": "novy@test.com", "role": "CUSTOMER"}
            ).encode()
        )
        .rstrip(b"=")
        .decode()
    )
    fake_access_token = f"{header}.{payload}.fakesig"
    mock_register_response = {
        "accessToken": fake_access_token,
        "refreshToken": "fake_refresh",
        "tokenType": "Bearer",
        "expiresInSeconds": 3600,
    }
    mock_update_response = {
        "id": 123,
        "email": "novy@test.com",
        "role": "EMPLOYEE",
        "active": True,
        "courier": True,
    }

    mocker.patch(
        "desktop_alkozon.features.employees.service.api_client.post",
        return_value=mock_register_response,
    )
    mocker.patch(
        "desktop_alkozon.features.employees.service.api_client.put",
        return_value=mock_update_response,
    )

    result = await employees_service.create_employee_account(
        "novy@test.com", "StrongPass1!", "Jan", "Kowalski", courier=True
    )

    assert result is not None
    assert result.id == 123
    assert result.email == "novy@test.com"
    assert result.role == "EMPLOYEE"
    assert result.courier is True


@pytest.mark.asyncio
async def test_create_employee_account_offline_enqueues_outbox(
    employees_service, mocker
):
    from desktop_alkozon.core.exceptions import OfflineError

    mocker.patch(
        "desktop_alkozon.features.employees.service.api_client.post",
        side_effect=OfflineError("Offline"),
    )
    mock_enqueue = mocker.patch(
        "desktop_alkozon.features.employees.service.enqueue",
    )

    result = await employees_service.create_employee_account(
        "novy@test.com", "StrongPass1!", "Jan", "Kowalski", courier=True, role="MANAGER"
    )

    assert result is None
    mock_enqueue.assert_called_once_with(
        "create_employee",
        "POST",
        "/auth/register",
        entity_id=None,
        request_body={
            "register": {
                "email": "novy@test.com",
                "password": "StrongPass1!",
                "firstName": "Jan",
                "lastName": "Kowalski",
                "ageConfirmed": True,
                "adultConfirmed": True,
            },
            "update": {
                "role": "MANAGER",
                "active": True,
                "courier": True,
            },
        },
        db_path=mocker.ANY,
    )


@pytest.mark.asyncio
async def test_create_employee_account_register_fails(employees_service, mocker):
    mocker.patch(
        "desktop_alkozon.features.employees.service.api_client.post",
        side_effect=Exception("API error"),
    )

    result = await employees_service.create_employee_account(
        "novy@test.com", "StrongPass1!"
    )

    assert result is None


def test_controller_has_create_employee_account(employees_controller):
    assert hasattr(employees_controller, "create_employee_account")


def test_controller_has_update_user(employees_controller):
    assert hasattr(employees_controller, "update_user")


def test_controller_has_get_all_users(employees_controller):
    assert hasattr(employees_controller, "get_all_users")
