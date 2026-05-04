import pytest
from desktop_alkozon.features.warehouse.service import WarehouseService
from desktop_alkozon.models.api_models import InventoryOverviewResponse, InventoryProductRow


@pytest.fixture
def warehouse_service():
    return WarehouseService()


def test_get_all_items_sync(warehouse_service):
    items = warehouse_service.get_all_items_sync()
    assert items is None or isinstance(items, InventoryOverviewResponse)


def test_warehouse_item_model():
    item = InventoryProductRow(productId=1, name="Piwo 0.5l", quantity=100, warehouseZone="A1")
    
    assert item.productId == 1
    assert item.name == "Piwo 0.5l"
    assert item.quantity == 100


def test_warehouse_item_optional_fields():
    item = InventoryProductRow(productId=1, name="Test", quantity=10)
    assert item.warehouseZone is None


@pytest.mark.asyncio
async def test_get_all_items_async(warehouse_service, mocker):
    mock_response = {
        "products": [{"productId": 1, "name": "Piwo", "quantity": 100, "warehouseZone": "A1"}],
        "rawMaterials": [{"id": 1, "name": "Jeczmien", "unit": "kg", "quantity": 500.0}]
    }
    mocker.patch("desktop_alkozon.features.warehouse.service.api_client.get", return_value=mock_response)
    
    result = await warehouse_service.get_all_items()
    assert result is not None
    assert isinstance(result, InventoryOverviewResponse)


@pytest.mark.asyncio
async def test_get_all_items_fallback_on_error(warehouse_service, mocker):
    mocker.patch("desktop_alkozon.features.warehouse.service.api_client.get", side_effect=Exception("API Error"))
    
    result = await warehouse_service.get_all_items()
    assert result is None
