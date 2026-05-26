from unittest.mock import MagicMock

import pytest

from desktop_alkozon.features.employees.controller import EmployeesController
from desktop_alkozon.features.employees.views import (
    create_employee_list_view,
    create_employees_view,
    create_job_offers_view,
)


class TestEmployeesHubView:
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

    def test_hub_view_has_navigation_buttons(self, mock_page):
        view = create_employees_view(mock_page)
        content = view.content.controls
        buttons = [c for c in content if hasattr(c, "on_click")]
        assert len(buttons) > 0

    def test_hub_view_has_title(self, mock_page):
        view = create_employees_view(mock_page)
        content = view.content.controls
        texts = [
            c for c in content if hasattr(c, "value") and "Pracownicy" in str(c.value)
        ]
        assert len(texts) > 0


def _flatten_controls(controls):
    result = []
    for c in controls:
        result.append(c)
        if hasattr(c, "controls") and c.controls:
            result.extend(_flatten_controls(c.controls))
    return result


class TestJobOffersView:
    @pytest.fixture
    def mock_page(self):
        page = MagicMock()
        page.overlay = []
        page.update = MagicMock()
        page.clean = MagicMock()
        page.add = MagicMock()
        page.run_task = MagicMock()
        return page

    def test_create_job_offers_view_returns_container(self, mock_page):
        view = create_job_offers_view(mock_page)
        assert view is not None
        assert hasattr(view, "content")

    def test_job_offers_view_has_offers_table(self, mock_page):
        view = create_job_offers_view(mock_page)
        content = _flatten_controls(view.content.controls)
        has_table = any(hasattr(c, "columns") for c in content)
        assert has_table

    def test_job_offers_view_has_title_field(self, mock_page):
        view = create_job_offers_view(mock_page)
        content = _flatten_controls(view.content.controls)
        fields = [c for c in content if hasattr(c, "label")]
        field_labels = [c.label for c in fields if hasattr(c, "label")]
        assert any("Tytul" in label for label in field_labels)

    def test_job_offers_view_has_post_offer_button(self, mock_page):
        view = create_job_offers_view(mock_page)
        content = _flatten_controls(view.content.controls)
        buttons = [c for c in content if hasattr(c, "on_click")]
        assert len(buttons) > 0

    def test_job_offers_view_has_back_button(self, mock_page):
        view = create_job_offers_view(mock_page)
        content = _flatten_controls(view.content.controls)
        buttons = [c for c in content if hasattr(c, "on_click")]
        assert len(buttons) > 0


class TestEmployeeListView:
    @pytest.fixture
    def mock_page(self):
        page = MagicMock()
        page.overlay = []
        page.update = MagicMock()
        page.clean = MagicMock()
        page.add = MagicMock()
        page.run_task = MagicMock()
        return page

    def test_create_employee_list_view_returns_container(self, mock_page):
        view = create_employee_list_view(mock_page)
        assert view is not None
        assert hasattr(view, "content")

    def test_employee_list_view_has_table(self, mock_page):
        view = create_employee_list_view(mock_page)
        content = _flatten_controls(view.content.controls)
        has_table = any(hasattr(c, "columns") for c in content)
        assert has_table

    def test_employee_list_view_has_email_field(self, mock_page):
        view = create_employee_list_view(mock_page)
        content = view.content.controls
        fields = [c for c in content if hasattr(c, "label")]
        field_labels = [c.label for c in fields if hasattr(c, "label")]
        assert any("Email" in label for label in field_labels)

    def test_employee_list_view_has_password_field(self, mock_page):
        view = create_employee_list_view(mock_page)
        content = view.content.controls
        fields = [c for c in content if hasattr(c, "label")]
        field_labels = [c.label for c in fields if hasattr(c, "label")]
        assert any("Haslo" in label for label in field_labels)

    def test_employee_list_view_has_create_button(self, mock_page):
        view = create_employee_list_view(mock_page)
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

    def test_controller_has_create_employee_account_method(self):
        controller = EmployeesController()
        assert hasattr(controller, "create_employee_account")

    def test_controller_has_update_user_method(self):
        controller = EmployeesController()
        assert hasattr(controller, "update_user")

    def test_controller_has_hire_method(self):
        controller = EmployeesController()
        assert hasattr(controller, "hire")

    def test_controller_has_terminate_method(self):
        controller = EmployeesController()
        assert hasattr(controller, "terminate")
