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
    def login_page(self, mock_page, mocker):
        mocker.patch("desktop_alkozon.core.auth.keyring.get_password", return_value=None)
        mocker.patch("desktop_alkozon.core.auth.keyring.set_password")
        mocker.patch("desktop_alkozon.core.auth.keyring.delete_password")
        mocker.patch("desktop_alkozon.core.logger.setup_logger")
        from desktop_alkozon.ui.pages.login_page import LoginPage
        return LoginPage(mock_page)

    def test_login_page_initializes_fields(self, login_page):
        assert login_page.username_field is not None
        assert login_page.password_field is not None
        assert login_page.two_fa_field is not None
        assert login_page.login_button is not None

    def test_username_field_max_length(self, login_page):
        assert login_page.username_field.max_length == 50

    def test_password_field_max_length(self, login_page):
        assert login_page.password_field.max_length == 128

    def test_two_fa_field_hidden_by_default(self, login_page):
        assert login_page.two_fa_field.visible is False

    def test_login_failure_shows_snackbar(self, login_page, mock_page, mocker):
        mocker.patch("desktop_alkozon.core.auth.keyring.get_password", return_value=None)
        
        login_page.username_field.value = "wrong"
        login_page.password_field.value = "short"
        
        login_page.login_clicked(MagicMock())
        
        assert len(mock_page.overlay) > 0

    def test_login_button_exists(self, login_page):
        assert login_page.login_button is not None


class TestMainMenuView:
    @pytest.fixture
    def mock_page(self):
        page = MagicMock()
        page.update = MagicMock()
        return page

    @pytest.fixture
    def main_menu(self, mock_page):
        from desktop_alkozon.ui.pages.main_menu import MainMenuView
        return MainMenuView(mock_page)

    def test_main_menu_has_three_buttons(self, main_menu):
        buttons = [ctrl for ctrl in main_menu.content.controls 
                   if hasattr(ctrl, "on_click")]
        assert len(buttons) >= 3

    def test_navigate_to_warehouse(self, main_menu, mock_page, mocker):
        mocker.patch("desktop_alkozon.features.warehouse.views.WarehouseView")
        
        main_menu._go_to_warehouse(MagicMock())
        
        mock_page.clean.assert_called_once()
        mock_page.add.assert_called_once()

    def test_navigate_to_deliveries(self, main_menu, mock_page, mocker):
        mocker.patch("desktop_alkozon.features.deliveries.views.DeliveriesView")
        
        main_menu._go_to_deliveries(MagicMock())
        
        mock_page.clean.assert_called_once()
        mock_page.add.assert_called_once()

    def test_navigate_to_employees(self, main_menu, mock_page, mocker):
        mocker.patch("desktop_alkozon.features.employees.views.EmployeesView")
        
        main_menu._go_to_employees(MagicMock())
        
        mock_page.clean.assert_called_once()
        mock_page.add.assert_called_once()
