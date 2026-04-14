import pytest
import asyncio


class TestAuthFlow:
    def test_auth_service_instantiation(self, mocker):
        mocker.patch("desktop_alkozon.core.auth.keyring.get_password", return_value=None)
        mocker.patch("desktop_alkozon.core.auth.keyring.set_password")
        mocker.patch("desktop_alkozon.core.auth.keyring.delete_password")
        
        from desktop_alkozon.core.auth import AuthService
        
        auth = AuthService()
        assert isinstance(auth, AuthService)
        assert hasattr(auth, "login")
        assert hasattr(auth, "logout")


class TestApiServiceIntegration:
    @pytest.mark.asyncio
    async def test_api_client_initialization(self, mocker):
        mocker.patch("desktop_alkozon.services.api_client.load_dotenv")
        mocker.patch.dict("os.environ", {"API_BASE_URL": "https://api.test.com"}, clear=True)
        
        from desktop_alkozon.services.api_client import ApiClient
        
        client = ApiClient()
        assert client.base_url == "https://api.test.com"

    @pytest.mark.asyncio
    async def test_multiple_concurrent_requests(self, mocker):
        mocker.patch("desktop_alkozon.services.api_client.load_dotenv")
        
        from desktop_alkozon.services.api_client import ApiClient
        from unittest.mock import AsyncMock, MagicMock
        
        client = ApiClient()
        client.client = AsyncMock()
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": "test"}
        client.client.get.return_value = mock_response
        
        results = await asyncio.gather(
            client.get("/test1"),
            client.get("/test2"),
            client.get("/test3")
        )
        
        assert len(results) == 3


class TestFeatureIntegration:
    def test_employees_hire_flow(self):
        from desktop_alkozon.features.employees.controller import EmployeesController
        
        controller = EmployeesController()
        initial_employees = len(controller.get_employees())
        
        controller.create_offer("Nowe Stanowisko", 4500.0)
        controller.hire(999, "Nowy Pracownik")
        
        assert len(controller.get_employees()) == initial_employees

    def test_warehouse_order_flow(self):
        from desktop_alkozon.features.warehouse.controller import WarehouseController
        
        controller = WarehouseController()
        initial_stock = len(controller.get_stock_data())
        
        item = controller.order_new_item("Nowy Produkt", 100, "szt.", 29.99)
        
        assert len(controller.get_stock_data()) == initial_stock + 1
        assert item.name == "Nowy Produkt"

    def test_deliveries_create_flow(self):
        from desktop_alkozon.features.deliveries.controller import DeliveriesController
        
        controller = DeliveriesController()
        initial_deliveries = len(controller.get_deliveries())
        
        delivery = controller.create_new_announcement(
            courier_name="Test Kurier",
            destination="Warszawa",
            announcement="Testowa dostawa"
        )
        
        assert len(controller.get_deliveries()) == initial_deliveries + 1
        assert delivery.courier_name == "Test Kurier"


class TestSessionPersistence:
    def test_auth_token_storage_contract(self, mocker):
        mock_set = mocker.patch("desktop_alkozon.core.auth.keyring.set_password")
        mock_get = mocker.patch("desktop_alkozon.core.auth.keyring.get_password", return_value=None)
        mock_delete = mocker.patch("desktop_alkozon.core.auth.keyring.delete_password")
        
        from desktop_alkozon.core.auth import AuthService
        
        auth = AuthService()
        auth.login("admin", "password123")
        
        mock_set.assert_called_with("desktop_alkozon", "auth_token", mocker.ANY)
