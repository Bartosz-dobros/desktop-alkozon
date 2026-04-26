import pytest
from desktop_alkozon.features.deliveries.service import DeliveriesService, Courier, Delivery, DeliveryAnnouncement


@pytest.fixture
def deliveries_service():
    return DeliveriesService()


def test_get_couriers_sync(deliveries_service):
    couriers = deliveries_service.get_couriers_sync()
    
    assert len(couriers) == 3
    assert all(isinstance(c, Courier) for c in couriers)


def test_get_deliveries_sync(deliveries_service):
    deliveries = deliveries_service.get_deliveries_sync()
    
    assert len(deliveries) == 1
    assert all(isinstance(d, Delivery) for d in deliveries)


def test_courier_model():
    courier = Courier(id=1, name="Jan Kowalski", email="jan@example.com", status="Dostępny", vehicle="Van")
    
    assert courier.id == 1
    assert courier.name == "Jan Kowalski"
    assert courier.status == "Dostępny"
    assert courier.vehicle == "Van"


def test_delivery_model():
    delivery = Delivery(id=1, courier_name="Jan", destination="Warszawa", status="W drodze", announcement="Test")
    
    assert delivery.id == 1
    assert delivery.destination == "Warszawa"
    assert delivery.status == "W drodze"


def test_delivery_announcement_model():
    announcement = DeliveryAnnouncement(id=1, title="Test", content="Content")
    
    assert announcement.id == 1
    assert announcement.title == "Test"


@pytest.mark.asyncio
async def test_get_couriers_async(deliveries_service, mocker):
    mock_response = [
        {"id": 1, "email": "jan@example.com", "firstName": "Jan", "lastName": "Kowalski", "role": "EMPLOYEE", "isActive": True},
    ]
    mocker.patch("desktop_alkozon.features.deliveries.service.api_client.get", return_value=mock_response)
    
    couriers = await deliveries_service.get_couriers()
    
    assert len(couriers) == 1


@pytest.mark.asyncio
async def test_get_deliveries_async(deliveries_service, mocker):
    mock_response = [
        {"id": 1, "orderId": 100, "status": "IN_TRANSIT", "addressSnapshot": "Warszawa"},
    ]
    mocker.patch("desktop_alkozon.features.deliveries.service.api_client.get", return_value=mock_response)
    
    deliveries = await deliveries_service.get_deliveries()
    
    assert len(deliveries) == 1
