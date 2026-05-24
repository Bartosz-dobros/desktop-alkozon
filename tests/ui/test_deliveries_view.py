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

    def test_deliveries_view_has_couriers_table(self, mock_page):
        view = create_deliveries_view(mock_page)
        content = view.content.controls
        has_table = any(hasattr(c, "columns") for c in content)
        assert has_table

    def test_deliveries_view_has_deliveries_table(self, mock_page):
        view = create_deliveries_view(mock_page)
        content = view.content.controls
        tables = [c for c in content if hasattr(c, "columns")]
        assert len(tables) >= 2

    def test_deliveries_view_has_announcements_table(self, mock_page):
        view = create_deliveries_view(mock_page)
        content = view.content.controls
        tables = [c for c in content if hasattr(c, "columns")]
        assert len(tables) >= 3

    def test_deliveries_view_has_courier_dropdown(self, mock_page):
        view = create_deliveries_view(mock_page)
        content = view.content.controls
        dropdowns = [c for c in content if hasattr(c, "options")]
        assert len(dropdowns) > 0

    def test_deliveries_view_has_destination_field(self, mock_page):
        view = create_deliveries_view(mock_page)
        content = view.content.controls
        fields = [c for c in content if hasattr(c, "label")]
        field_labels = [c.label for c in fields if hasattr(c, "label")]
        assert any("Cel dostawy" in label for label in field_labels)

    def test_deliveries_view_has_announcement_field(self, mock_page):
        view = create_deliveries_view(mock_page)
        content = view.content.controls
        fields = [c for c in content if hasattr(c, "label")]
        field_labels = [c.label for c in fields if hasattr(c, "label")]
        assert any("Tresc" in label for label in field_labels)

    def test_deliveries_view_has_create_button(self, mock_page):
        view = create_deliveries_view(mock_page)
        content = view.content.controls
        buttons = [c for c in content if hasattr(c, "on_click")]
        assert len(buttons) > 0

    def test_deliveries_view_has_back_button(self, mock_page):
        view = create_deliveries_view(mock_page)
        content = view.content.controls
        buttons = [c for c in content if hasattr(c, "on_click")]
        assert len(buttons) > 0


class TestDeliveriesController:
    def test_controller_instantiation(self):
        controller = DeliveriesController()
        assert controller is not None
        assert hasattr(controller, "get_couriers")
        assert hasattr(controller, "get_deliveries")

    def test_controller_has_create_announcement_method(self):
        controller = DeliveriesController()
        assert hasattr(controller, "create_new_announcement")

    def test_controller_has_update_status_method(self):
        controller = DeliveriesController()
        assert hasattr(controller, "update_delivery_status")

    def test_controller_has_assign_courier_method(self):
        controller = DeliveriesController()
        assert hasattr(controller, "assign_courier")
