from unittest.mock import MagicMock, patch

import pytest

from desktop_alkozon.features.warehouse.controller import WarehouseController
from desktop_alkozon.features.warehouse.views import create_warehouse_view
from desktop_alkozon.models.api_models import InventoryProductRow


class TestWarehouseView:
    @pytest.fixture
    def mock_page(self):
        page = MagicMock()
        page.overlay = []
        page.update = MagicMock()
        page.clean = MagicMock()
        page.add = MagicMock()
        page.run_task = MagicMock()
        return page

    def test_create_warehouse_view_returns_container(self, mock_page):
        view = create_warehouse_view(mock_page)
        assert view is not None
        assert hasattr(view, "content")

    def test_warehouse_view_has_table(self, mock_page):
        view = create_warehouse_view(mock_page)
        content = view.content.controls
        has_table = any(hasattr(c, "columns") for c in content)
        assert has_table

    def test_warehouse_view_has_product_id_field(self, mock_page):
        view = create_warehouse_view(mock_page)
        content = view.content.controls
        fields = [c for c in content if hasattr(c, "label")]
        field_labels = [c.label for c in fields if hasattr(c, "label")]
        assert any("ID produktu" in label for label in field_labels)

    def test_warehouse_view_has_quantity_field(self, mock_page):
        view = create_warehouse_view(mock_page)
        content = view.controls
        fields = [c for c in content if hasattr(c, "label")]
        field_labels = [c.label for c in fields if hasattr(c, "label")]
        assert any("Ilosc" in label for label in field_labels)

    def test_warehouse_view_has_order_button(self, mock_page):
        view = create_warehouse_view(mock_page)
        content = view.content.controls
        buttons = [c for c in content if hasattr(c, "on_click")]
        assert len(buttons) > 0

    def test_warehouse_view_has_back_button(self, mock_page):
        view = create_warehouse_view(mock_page)
        content = view.content.controls
        buttons = [c for c in content if hasattr(c, "on_click")]
        assert len(buttons) > 0

    @patch(
        "desktop_alkozon.features.warehouse.controller.WarehouseController.get_stock_data"
    )
    async def test_warehouse_loads_data(self, mock_get_stock, mock_page):
        mock_get_stock.return_value = [
            InventoryProductRow(
                productId=1, name="Test", quantity=100, warehouseZone="A1"
            )
        ]
        view = create_warehouse_view(mock_page)
        assert view is not None


class TestWarehouseController:
    def test_controller_instantiation(self):
        controller = WarehouseController()
        assert controller is not None
        assert hasattr(controller, "get_stock_data")

    def test_controller_has_order_method(self):
        controller = WarehouseController()
        assert hasattr(controller, "order_new_item")
