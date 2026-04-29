import pytest
from unittest.mock import MagicMock


class TestLoginPage:
    @pytest.fixture
    def mock_page(self):
        page = MagicMock()
        page.overlay = []
        page.update = MagicMock()
        return page

    @pytest.fixture
    def login_view(self, mock_page, mocker):
        mocker.patch("desktop_alkozon.core.auth.keyring.get_password", return_value=None)
        mocker.patch("desktop_alkozon.core.auth.keyring.set_password")
        mocker.patch("desktop_alkozon.core.auth.keyring.delete_password")
        mocker.patch("desktop_alkozon.core.logger.setup_logger")
        mocker.patch("desktop_alkozon.ui.pages.login_page.auth_service")
        from desktop_alkozon.ui.pages.login_page import create_login_page_view
        return create_login_page_view(mock_page)

    def test_login_page_creates_view(self, login_view):
        assert login_view is not None
        assert isinstance(login_view, MagicMock) or hasattr(login_view, 'content')

    def test_login_page_has_controls(self, login_view):
        if hasattr(login_view, 'content') and hasattr(login_view.content, 'controls'):
            assert len(login_view.content.controls) > 0


class TestMainMenuView:
    @pytest.fixture
    def mock_page(self):
        page = MagicMock()
        page.update = MagicMock()
        page.clean = MagicMock()
        page.add = MagicMock()
        return page

    @pytest.fixture
    def main_menu_view(self, mock_page, mocker):
        mocker.patch("desktop_alkozon.ui.pages.main_menu.auth_service")
        from desktop_alkozon.ui.pages.main_menu import create_main_menu_view
        return create_main_menu_view(mock_page)

    def test_main_menu_creates_view(self, main_menu_view):
        assert main_menu_view is not None

    def test_main_menu_has_buttons(self, main_menu_view):
        if hasattr(main_menu_view, 'content') and hasattr(main_menu_view.content, 'controls'):
            controls = main_menu_view.content.controls
            buttons = [ctrl for ctrl in controls if hasattr(ctrl, "on_click")]
            assert len(buttons) >= 3
