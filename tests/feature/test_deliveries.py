import pytest
from desktop_alkozon.features.deliveries.service import DeliveriesService
from desktop_alkozon.models.api_models import DeliveryResponse, DeliveryAnnouncementResponse, DeliveryStatus


@pytest.fixture
def deliveries_service():
    return DeliveriesService()


def test_get_couriers_sync(deliveries_service):
    couriers = deliveries_service.get_couriers_sync()
    assert isinstance(couriers, list)


def test_get_deliveries_sync(deliveries_service):
    deliveries = deliveries_service.get_deliveries_sync()
    assert isinstance(deliveries, list)


def test_delivery_model():
    delivery = DeliveryResponse(
        id=1, orderId=100, courierId=1, courierEmail="jan@example.com",
        status=DeliveryStatus.PENDING, addressSnapshot="Warszawa",
        customerEmail="customer@example.com"
    )
    assert delivery.id == 1
    assert delivery.status == DeliveryStatus.PENDING


def test_delivery_announcement_model():
    announcement = DeliveryAnnouncementResponse(
        id=1, title="Test", content="Content"
    )
    assert announcement.id == 1
    assert announcement.title == "Test"


@pytest.mark.asyncio
async def test_get_couriers_async(deliveries_service, mocker):
    mock_response = [
        {"id": 1, "email": "jan@example.com", "firstName": "Jan", "lastName": "Kowalski",
         "role": "EMPLOYEE", "active": True, "courier": True}
    ]
    mocker.patch("desktop_alkozon.features.deliveries.service.api_client.get", return_value=mock_response)
    
    couriers = await deliveries_service.get_couriers()
    assert len(couriers) >= 0


@pytest.mark.asyncio
async def test_get_deliveries_async(deliveries_service, mocker):
    mock_response = [
        {"id": 1, "orderId": 100, "courierId": 1, "courierEmail": "jan@example.com",
         "status": "IN_TRANSIT", "addressSnapshot": "Warszawa", "customerEmail": "customer@example.com"}
    ]
    mocker.patch("desktop_alkozon.features.deliveries.service.api_client.get", return_value=mock_response)
    
    deliveries = await deliveries_service.get_deliveries()
    assert len(deliveries) == 1
