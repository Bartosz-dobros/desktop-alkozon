from unittest.mock import MagicMock

import flet as ft
import pytest

from desktop_alkozon.core.auth import auth_service
from desktop_alkozon.ui.pages.login_page import (
    create_login_page_view,
    create_main_menu_view,
)


def _get_content_controls(view):
    if hasattr(view, "content"):
        return view.content.controls
    return view.controls[0].content.controls


class TestLoginPageView:
    @pytest.fixture
    def mock_page(self):
        page = MagicMock()
        page.overlay = []
        page.update = MagicMock()
        page.clean = MagicMock()
        page.add = MagicMock()
        page.run_task = MagicMock()
        return page

    @pytest.fixture
    def mock_auth_service(self, mocker):
        mocker.patch(
            "desktop_alkozon.core.auth.keyring.get_password", return_value=None
        )
        mocker.patch("desktop_alkozon.core.auth.keyring.set_password")
        mocker.patch("desktop_alkozon.core.auth.keyring.delete_password")
        return auth_service

    def test_create_login_page_returns_container(self, mock_page):
        view = create_login_page_view(mock_page)
        assert view is not None
        assert hasattr(view, "controls")

    def test_login_page_has_username_field(self, mock_page):
        view = create_login_page_view(mock_page)
        controls = _get_content_controls(view)
        assert any(hasattr(c, "label") and "użytkownika" in c.label for c in controls)

    def test_login_page_has_password_field(self, mock_page):
        view = create_login_page_view(mock_page)
        controls = _get_content_controls(view)
        assert any(hasattr(c, "label") and "Hasło" in c.label for c in controls)

    def test_login_page_has_login_button(self, mock_page):
        view = create_login_page_view(mock_page)
        controls = _get_content_controls(view)
        assert any(
            hasattr(c, "content")
            and hasattr(c.content, "value")
            and c.content.value == "ZALOGUJ"
            for c in controls
        )

    def test_login_page_has_forgot_password_button(self, mock_page):
        view = create_login_page_view(mock_page)
        controls = _get_content_controls(view)
        assert any(hasattr(c, "on_click") for c in controls)

    # Demo mode button test removed as unnecessary


class TestMainMenuView:
    @pytest.fixture
    def mock_page(self):
        page = MagicMock()
        page.clean = MagicMock()
        page.add = MagicMock()
        page.update = MagicMock()
        return page

    @pytest.fixture
    def mock_auth_service(self, mocker):
        mocker.patch(
            "desktop_alkozon.core.auth.keyring.get_password", return_value=None
        )
        auth_service.attempts = 0
        auth_service.locked = False
        auth_service._current_user = {
            "id": 1,
            "email": "test@example.com",
            "role": "MANAGER",
            "firstName": "Test",
            "lastName": "User",
        }
        return auth_service

    def test_create_main_menu_returns_container(self, mock_page):
        view = create_main_menu_view(mock_page)
        assert view is not None
        assert hasattr(view, "controls")

    def test_main_menu_shows_user_name(self, mock_page):
        view = create_main_menu_view(mock_page)
        controls = _get_content_controls(view)
        user_text = [
            c for c in controls if hasattr(c, "value") and "Zalogowany" in c.value
        ]
        assert len(user_text) > 0

    def test_main_menu_has_warehouse_button(self, mock_page):
        view = create_main_menu_view(mock_page)
        controls = _get_content_controls(view)
        buttons = [c for c in controls if hasattr(c, "on_click")]
        assert len(buttons) >= 3

    def test_main_menu_has_logout_button(self, mock_page):
        view = create_main_menu_view(mock_page)
        controls = _get_content_controls(view)
        logout_buttons = [
            c for c in controls if hasattr(c, "icon") and c.icon == ft.Icons.LOGOUT
        ]
        assert len(logout_buttons) > 0


class TestLoginPageWithMockAuth:
    @pytest.fixture
    def mock_page(self):
        page = MagicMock()
        page.overlay = []
        page.update = MagicMock()
        page.clean = MagicMock()
        page.add = MagicMock()
        page.run_task = MagicMock()
        return page

    def test_login_page_creates_with_auth_service(self, mock_page, mocker):
        mocker.patch(
            "desktop_alkozon.core.auth.keyring.get_password", return_value=None
        )
        view = create_login_page_view(mock_page)
        assert view is not None

    def test_login_page_verification_field_exists(self, mock_page):
        view = create_login_page_view(mock_page)
        controls = _get_content_controls(view)
        verification_fields = [
            c for c in controls if hasattr(c, "label") and "weryfikacyjny" in c.label
        ]
        assert len(verification_fields) > 0

    def test_login_page_status_text_exists(self, mock_page):
        view = create_login_page_view(mock_page)
        controls = _get_content_controls(view)
        status_fields = [
            c for c in controls if hasattr(c, "color") and c.color == ft.Colors.RED
        ]
        assert len(status_fields) > 0
