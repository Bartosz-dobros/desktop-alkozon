import pytest
from desktop_alkozon.features.warehouse.service import WarehouseService, WarehouseItem


@pytest.fixture
def warehouse_service():
    return WarehouseService()


def test_get_all_items_sync(warehouse_service):
    items = warehouse_service.get_all_items_sync()
    
    assert len(items) == 4
    assert all(isinstance(item, WarehouseItem) for item in items)


def test_warehouse_item_model():
    item = WarehouseItem(id=1, name="Piwo 0.5l", quantity=100, unit="szt.", price=4.99, category="Piwo")
    
    assert item.id == 1
    assert item.name == "Piwo 0.5l"
    assert item.quantity == 100
    assert item.unit == "szt."
    assert item.price == 4.99
    assert item.category == "Piwo"


def test_warehouse_item_optional_fields():
    item = WarehouseItem(id=1, name="Test", quantity=10, unit="szt.", price=9.99)
    
    assert item.category is None
    assert item.productId is None


@pytest.mark.asyncio
async def test_get_all_items_async(warehouse_service, mocker):
    mock_response = [
        {"id": 1, "quantity": 100, "product": {"name": "Piwo", "price": 4.99, "unit": "szt."}},
        {"id": 2, "quantity": 50, "product": {"name": "Wodka", "price": 29.99, "unit": "szt."}},
    ]
    mocker.patch("desktop_alkozon.features.warehouse.service.api_client.get", return_value=mock_response)
    
    items = await warehouse_service.get_all_items()
    
    assert len(items) == 2


@pytest.mark.asyncio
async def test_get_all_items_fallback_on_error(warehouse_service, mocker):
    mocker.patch("desktop_alkozon.features.warehouse.service.api_client.get", side_effect=Exception("API Error"))
    
    items = await warehouse_service.get_all_items()
    
    assert len(items) == 4
