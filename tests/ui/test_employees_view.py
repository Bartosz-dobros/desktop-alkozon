from unittest.mock import MagicMock

import pytest

from desktop_alkozon.features.employees.controller import EmployeesController
from desktop_alkozon.features.employees.views import create_employees_view


class TestEmployeesView:
    @pytest.fixture
    def mock_page(self):
        page = MagicMock()
        page.overlay = []
        page.update = MagicMock()
        page.clean = MagicMock()
        page.add = MagicMock()
        page.run_task = MagicMock()
        return page

    def test_create_employees_view_returns_container(self, mock_page):
        view = create_employees_view(mock_page)
        assert view is not None
        assert hasattr(view, "content")

    def test_employees_view_has_offers_table(self, mock_page):
        view = create_employees_view(mock_page)
        content = view.content.controls
        has_table = any(hasattr(c, "columns") for c in content)
        assert has_table

    def test_employees_view_has_employees_table(self, mock_page):
        view = create_employees_view(mock_page)
        content = view.content.controls
        tables = [c for c in content if hasattr(c, "columns")]
        assert len(tables) >= 2

    def test_employees_view_has_title_field(self, mock_page):
        view = create_employees_view(mock_page)
        content = view.content.controls
        fields = [c for c in content if hasattr(c, "label")]
        field_labels = [c.label for c in fields if hasattr(c, "label")]
        assert any("Tytul" in label for label in field_labels)

    def test_employees_view_has_post_offer_button(self, mock_page):
        view = create_employees_view(mock_page)
        content = view.content.controls
        buttons = [c for c in content if hasattr(c, "on_click")]
        assert len(buttons) > 0

    def test_employees_view_has_back_button(self, mock_page):
        view = create_employees_view(mock_page)
        content = view.content.controls
        buttons = [c for c in content if hasattr(c, "on_click")]
        assert len(buttons) > 0


class TestEmployeesController:
    def test_controller_instantiation(self):
        controller = EmployeesController()
        assert controller is not None
        assert hasattr(controller, "get_offers")
        assert hasattr(controller, "get_employees")

    def test_controller_has_create_offer_method(self):
        controller = EmployeesController()
        assert hasattr(controller, "create_offer")

    def test_controller_has_hire_method(self):
        controller = EmployeesController()
        assert hasattr(controller, "hire")

    def test_controller_has_terminate_method(self):
        controller = EmployeesController()
        assert hasattr(controller, "terminate")
