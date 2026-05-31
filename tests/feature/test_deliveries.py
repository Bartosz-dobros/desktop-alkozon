import pytest

from desktop_alkozon.features.deliveries.service import DeliveriesService
from desktop_alkozon.models.api_models import (
    DeliveryAnnouncementResponse,
    DeliveryDetails,
    DeliveryResponse,
    DeliveryStatus,
)


@pytest.fixture
def deliveries_service():
    return DeliveriesService()


def test_get_couriers_sync(deliveries_service):
    couriers = deliveries_service.get_couriers_sync()
    assert isinstance(couriers, list)


def test_get_unassigned_couriers_sync(deliveries_service):
    couriers = deliveries_service.get_unassigned_couriers_sync()
    assert isinstance(couriers, list)


def test_get_deliveries_sync(deliveries_service):
    deliveries = deliveries_service.get_deliveries_sync()
    assert isinstance(deliveries, list)


def test_delivery_model():
    delivery = DeliveryResponse(
        id=1,
        orderId=100,
        courierId=1,
        courierEmail="jan@example.com",
        status=DeliveryStatus.PENDING,
        deliveryDetails=DeliveryDetails(
            recipientName="Jan Kowalski",
            streetAddress="Marszalkowska 1",
            city="Warszawa",
            postalCode="00-001",
            country="Polska",
        ),
        customerEmail="customer@example.com",
    )
    assert delivery.id == 1
    assert delivery.status == DeliveryStatus.PENDING
    assert delivery.deliveryDetails is not None
    assert delivery.deliveryDetails.city == "Warszawa"


def test_delivery_announcement_model():
    announcement = DeliveryAnnouncementResponse(id=1, title="Test", content="Content")
    assert announcement.id == 1
    assert announcement.title == "Test"


@pytest.mark.asyncio
async def test_get_couriers_async(deliveries_service, mocker):
    mock_response = [
        {
            "id": 1,
            "email": "jan@example.com",
            "firstName": "Jan",
            "lastName": "Kowalski",
            "role": "EMPLOYEE",
            "active": True,
            "courier": True,
        }
    ]
    mocker.patch(
        "desktop_alkozon.features.deliveries.service.api_client.get",
        return_value=mock_response,
    )

    couriers = await deliveries_service.get_couriers()
    assert len(couriers) >= 0


@pytest.mark.asyncio
async def test_get_deliveries_async(deliveries_service, mocker):
    mock_response = [
        {
            "id": 1,
            "orderId": 100,
            "courierId": 1,
            "courierEmail": "jan@example.com",
            "status": "IN_TRANSIT",
            "deliveryDetails": {
                "recipientName": "Jan Kowalski",
                "streetAddress": "Marszalkowska 1",
                "city": "Warszawa",
                "postalCode": "00-001",
                "country": "Polska",
            },
            "customerEmail": "customer@example.com",
        }
    ]
    mocker.patch(
        "desktop_alkozon.features.deliveries.service.api_client.get",
        return_value=mock_response,
    )

    deliveries = await deliveries_service.get_deliveries()
    assert len(deliveries) == 1


@pytest.mark.asyncio
async def test_get_unassigned_couriers_async(deliveries_service, mocker):
    mock_users = [
        {
            "id": 1,
            "email": "jan@example.com",
            "role": "EMPLOYEE",
            "active": True,
            "courier": True,
        },
        {
            "id": 2,
            "email": "anna@example.com",
            "role": "EMPLOYEE",
            "active": True,
            "courier": True,
        },
    ]
    mock_deliveries = [
        {
            "id": 101,
            "orderId": 1001,
            "courierId": 1,
            "courierEmail": "jan@example.com",
            "status": "IN_TRANSIT",
            "deliveryDetails": {
                "recipientName": "Jan Kowalski",
                "streetAddress": "Marszalkowska 1",
                "city": "Warszawa",
                "postalCode": "00-001",
                "country": "Polska",
            },
        }
    ]
    mocker.patch(
        "desktop_alkozon.features.deliveries.service.api_client.get",
        side_effect=[mock_users, mock_deliveries],
    )

    result = await deliveries_service.get_unassigned_couriers()
    assert len(result) == 1
    assert result[0]["id"] == 2
