import pytest
from desktop_alkozon.features.warehouse.service import WarehouseService, WarehouseItem


@pytest.fixture
def warehouse_service():
    return WarehouseService()


def test_get_all_items(warehouse_service):
    items = warehouse_service.get_all_items()
    
    assert len(items) == 4
    assert all(isinstance(item, WarehouseItem) for item in items)


def test_add_new_item(warehouse_service):
    new_item = warehouse_service.add_new_item("Wino 0.75l", 50, "szt.", 39.99)
    
    assert new_item.name == "Wino 0.75l"
    assert new_item.quantity == 50
    assert new_item.price == 39.99
    assert len(warehouse_service.get_all_items()) == 5


def test_warehouse_item_model():
    item = WarehouseItem(id=1, name="Test", quantity=10, unit="szt.", price=9.99)
    
    assert item.id == 1
    assert item.name == "Test"
    assert item.quantity == 10
    assert item.unit == "szt."
    assert item.price == 9.99
