import pytest
from desktop_alkozon.features.deliveries.service import DeliveriesService, Courier, Delivery


@pytest.fixture
def deliveries_service():
    return DeliveriesService()


def test_get_couriers(deliveries_service):
    couriers = deliveries_service.get_couriers()
    
    assert len(couriers) == 3
    assert all(isinstance(c, Courier) for c in couriers)


def test_get_deliveries(deliveries_service):
    deliveries = deliveries_service.get_deliveries()
    
    assert len(deliveries) == 1
    assert all(isinstance(d, Delivery) for d in deliveries)


def test_create_announcement(deliveries_service):
    new_delivery = deliveries_service.create_announcement(
        courier_name="Anna Nowak",
        destination="Kraków",
        announcement="Dostawa alkoholu premium"
    )
    
    assert new_delivery.courier_name == "Anna Nowak"
    assert new_delivery.destination == "Kraków"
    assert new_delivery.status == "Nowa"
    assert len(deliveries_service.get_deliveries()) == 2


def test_courier_model():
    courier = Courier(id=1, name="Test Courier", status="Dostępny", vehicle="Van")
    
    assert courier.id == 1
    assert courier.name == "Test Courier"
    assert courier.status == "Dostępny"
    assert courier.vehicle == "Van"


def test_delivery_model():
    delivery = Delivery(
        id=1,
        courier_name="Test",
        destination="Warszawa",
        status="W drodze",
        announcement="Test"
    )
    
    assert delivery.id == 1
    assert delivery.destination == "Warszawa"
