from unittest.mock import MagicMock

import pytest

from desktop_alkozon.features.deliveries.controller import DeliveriesController
from desktop_alkozon.features.deliveries.views import create_deliveries_view


class TestDeliveriesView:
    @pytest.fixture
    def mock_page(self):
        page = MagicMock()
        page.overlay = []
        page.update = MagicMock()
        page.clean = MagicMock()
        page.add = MagicMock()
        page.run_task = MagicMock()
        return page

    def test_create_deliveries_view_returns_container(self, mock_page):
        view = create_deliveries_view(mock_page)
        assert view is not None
        assert hasattr(view, "content")

    def test_deliveries_view_has_deliveries_table(self, mock_page):
        view = create_deliveries_view(mock_page)
        content = view.content.controls
        tables = [c for c in content if hasattr(c, "columns")]
        assert len(tables) >= 1

    def test_deliveries_view_has_couriers_table(self, mock_page):
        view = create_deliveries_view(mock_page)
        content = view.content.controls
        tables = [c for c in content if hasattr(c, "columns")]
        assert len(tables) >= 2

    def test_deliveries_view_has_selected_text(self, mock_page):
        view = create_deliveries_view(mock_page)
        content = view.content.controls
        texts = [c for c in content if hasattr(c, "value")]
        assert any("Zadna" in str(t.value) for t in texts)

    def test_deliveries_view_has_back_button(self, mock_page):
        view = create_deliveries_view(mock_page)
        content = view.content.controls
        buttons = [c for c in content if hasattr(c, "on_click")]
        assert len(buttons) > 0


class TestDeliveriesController:
    def test_controller_instantiation(self):
        controller = DeliveriesController()
        assert controller is not None
        assert hasattr(controller, "get_deliveries")

    def test_controller_has_get_unassigned_couriers_method(self):
        controller = DeliveriesController()
        assert hasattr(controller, "get_unassigned_couriers")

    def test_controller_has_assign_courier_method(self):
        controller = DeliveriesController()
        assert hasattr(controller, "assign_courier")
