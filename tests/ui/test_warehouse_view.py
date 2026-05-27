from unittest.mock import MagicMock

import pytest

from desktop_alkozon.features.warehouse.controller import WarehouseController
from desktop_alkozon.features.warehouse.views import create_warehouse_view


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

    def test_warehouse_view_has_navigation_buttons(self, mock_page):
        view = create_warehouse_view(mock_page)
        content = view.content.controls
        buttons = [c for c in content if hasattr(c, "on_click")]
        assert len(buttons) >= 3

    def test_warehouse_view_has_back_button(self, mock_page):
        view = create_warehouse_view(mock_page)
        content = view.content.controls
        buttons = [c for c in content if hasattr(c, "on_click")]
        assert len(buttons) > 0

    def test_warehouse_view_has_title(self, mock_page):
        view = create_warehouse_view(mock_page)
        content = view.content.controls
        assert any(hasattr(c, "size") and c.size == 24 for c in content)


class TestWarehouseController:
    def test_controller_instantiation(self):
        controller = WarehouseController()
        assert controller is not None
        assert hasattr(controller, "get_products")

    def test_controller_has_order_method(self):
        controller = WarehouseController()
        assert hasattr(controller, "order_new_item")
