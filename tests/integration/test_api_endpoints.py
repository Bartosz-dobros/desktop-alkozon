from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

import desktop_alkozon
from desktop_alkozon.features.deliveries.service import DeliveriesService
from desktop_alkozon.features.employees.service import EmployeesService
from desktop_alkozon.features.warehouse.service import WarehouseService
from desktop_alkozon.services.api_client import ApiClient


class TestApiEndpoints:
    @pytest.fixture
    def api_client(self, mocker):
        mocker.patch(
            "desktop_alkozon.services.api_client.load_config",
            return_value={"API_BASE_URL": "http://test:8080/api", "API_TIMEOUT": 10},
        )
        ApiClient._instance = None
        client = ApiClient()
        return client

    @pytest.fixture
    def mock_response(self):
        def _make_response(data, status_code=200):
            mock = MagicMock()
            mock.json.return_value = data
            mock.status_code = status_code
            mock.raise_for_status = MagicMock()
            return mock

        return _make_response

    @pytest.mark.asyncio
    async def test_auth_staff_login_endpoint(self, api_client, mock_response):
        mock_obj = mock_response(
            {
                "verificationRequired": False,
                "accessToken": "test_token",
                "refreshToken": "test_refresh",
                "tokenType": "Bearer",
                "expiresInSeconds": 900,
            }
        )
        api_client.client.request = AsyncMock(return_value=mock_obj)

        payload = {
            "email": "test@example.com",
            "password": "password123",
            "deviceId": "desktop-001",
        }
        result = await api_client.post("/auth/staff/login", payload)

        assert result["accessToken"] == "test_token"

    @pytest.mark.asyncio
    async def test_auth_staff_login_with_verification(self, api_client, mock_response):
        mock_obj = mock_response(
            {
                "verificationRequired": True,
                "challengeId": "challenge_123",
            }
        )
        api_client.client.request = AsyncMock(return_value=mock_obj)

        payload = {
            "email": "test@example.com",
            "password": "password123",
            "deviceId": "desktop-001",
        }
        result = await api_client.post("/auth/staff/login", payload)

        assert result["verificationRequired"] is True
        assert result["challengeId"] == "challenge_123"

    @pytest.mark.asyncio
    async def test_auth_verify_device_endpoint(self, api_client, mock_response):
        mock_obj = mock_response(
            {
                "accessToken": "verified_token",
                "refreshToken": "verified_refresh",
                "tokenType": "Bearer",
                "expiresInSeconds": 900,
            }
        )
        api_client.client.request = AsyncMock(return_value=mock_obj)

        payload = {
            "challengeId": "challenge_123",
            "deviceId": "desktop-001",
            "code": "1234",
        }
        result = await api_client.post("/auth/staff/verify-device", payload)

        assert result["accessToken"] == "verified_token"

    @pytest.mark.asyncio
    async def test_auth_refresh_endpoint(self, api_client, mock_response):
        mock_obj = mock_response(
            {
                "accessToken": "new_token",
                "refreshToken": "new_refresh",
                "tokenType": "Bearer",
                "expiresInSeconds": 900,
            }
        )
        api_client.client.request = AsyncMock(return_value=mock_obj)

        payload = {"refreshToken": "old_refresh"}
        result = await api_client.post("/auth/refresh", payload)

        assert result["accessToken"] == "new_token"

    @pytest.mark.asyncio
    async def test_admin_users_endpoint(self, api_client, mock_response):
        mock_obj = mock_response(
            [
                {
                    "id": 1,
                    "email": "jan@example.com",
                    "role": "EMPLOYEE",
                    "active": True,
                    "courier": True,
                }
            ]
        )
        api_client.client.request = AsyncMock(return_value=mock_obj)

        result = await api_client.get("/admin/users")
        assert isinstance(result, list)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_admin_job_offers_endpoint(self, api_client, mock_response):
        mock_obj = mock_response(
            [
                {
                    "id": 1,
                    "title": "Kierowca",
                    "description": "Test",
                    "status": "OPEN",
                    "createdAt": "2024-01-01T00:00:00Z",
                    "updatedAt": "2024-01-01T00:00:00Z",
                }
            ]
        )
        api_client.client.request = AsyncMock(return_value=mock_obj)

        result = await api_client.get("/admin/job-offers")
        assert isinstance(result, list)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_inventory_endpoint(self, api_client, mock_response):
        mock_obj = mock_response(
            {
                "products": [
                    {
                        "productId": 1,
                        "name": "Vodka",
                        "quantity": 100,
                        "warehouseZone": "A1",
                    }
                ],
                "rawMaterials": [
                    {"id": 1, "name": "Barley", "unit": "kg", "quantity": 500.0}
                ],
            }
        )
        api_client.client.request = AsyncMock(return_value=mock_obj)

        result = await api_client.get("/inventory")
        assert "products" in result
        assert "rawMaterials" in result

    @pytest.mark.asyncio
    async def test_deliveries_endpoint(self, api_client, mock_response):
        mock_obj = mock_response(
            [
                {
                    "id": 1,
                    "orderId": 100,
                    "courierId": 1,
                    "courierEmail": "jan@example.com",
                    "status": "IN_TRANSIT",
                    "addressSnapshot": "Warszawa",
                }
            ]
        )
        api_client.client.request = AsyncMock(return_value=mock_obj)

        result = await api_client.get("/deliveries")
        assert isinstance(result, list)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_post_job_offer(self, api_client, mock_response):
        mock_obj = mock_response(
            {
                "id": 1,
                "title": "Kierowca",
                "description": "Test",
                "status": "OPEN",
                "createdAt": "2024-01-01T00:00:00Z",
                "updatedAt": "2024-01-01T00:00:00Z",
            }
        )
        api_client.client.request = AsyncMock(return_value=mock_obj)

        payload = {"title": "Kierowca", "description": "Test"}
        result = await api_client.post("/admin/job-offers", payload)
        assert result["id"] == 1

    @pytest.mark.asyncio
    async def test_patch_delivery_status(self, api_client, mock_response):
        mock_obj = mock_response(
            {
                "id": 1,
                "orderId": 100,
                "courierId": 1,
                "courierEmail": "jan@example.com",
                "status": "DELIVERED",
                "addressSnapshot": "Warszawa",
            }
        )
        api_client.client.request = AsyncMock(return_value=mock_obj)

        payload = {"status": "DELIVERED"}
        result = await api_client.patch("/deliveries/1/status", payload)
        assert result["status"] == "DELIVERED"

    @pytest.mark.asyncio
    async def test_post_delivery_announcement(self, api_client, mock_response):
        mock_obj = mock_response(
            {
                "id": 1,
                "title": "Test",
                "content": "Content",
                "createdAt": "2024-01-01T00:00:00Z",
            }
        )
        api_client.client.request = AsyncMock(return_value=mock_obj)

        payload = {"title": "Test", "content": "Content"}
        result = await api_client.post("/admin/delivery-announcements", payload)
        assert result["id"] == 1

    @pytest.mark.asyncio
    async def test_patch_inventory_product(self, api_client, mock_response):
        mock_obj = mock_response(
            {
                "productId": 1,
                "name": "Vodka",
                "quantity": 150,
                "warehouseZone": "A1",
            }
        )
        api_client.client.request = AsyncMock(return_value=mock_obj)

        payload = {"delta": 50}
        result = await api_client.patch("/inventory/products/1", payload)
        assert result["quantity"] == 150

    @pytest.mark.asyncio
    async def test_delete_job_offer(self, api_client, mock_response):
        mock_obj = mock_response({})
        api_client.client.request = AsyncMock(return_value=mock_obj)

        result = await api_client.delete("/admin/job-offers/1")
        assert result == {}


class TestWarehouseApiIntegration:
    @pytest.mark.asyncio
    async def test_get_all_items_uses_inventory_endpoint(self, mocker):
        mocker.patch(
            "desktop_alkozon.services.api_client.load_config",
            return_value={"API_BASE_URL": "http://test:8080/api", "API_TIMEOUT": 10},
        )
        mocker.patch(
            "desktop_alkozon.services.api_client.api_client.client.request",
            new_callable=AsyncMock,
        )
        ApiClient._instance = None

        mock_response = {
            "products": [
                {"productId": 1, "name": "Test", "quantity": 100, "warehouseZone": "A1"}
            ],
            "rawMaterials": [],
        }
        desktop_alkozon.services.api_client.api_client.client.request.return_value = (
            MagicMock(
                json=MagicMock(return_value=mock_response),
                status_code=200,
                raise_for_status=MagicMock(),
            )
        )

        service = WarehouseService()
        result = await service.get_all_items()
        assert result is not None
        assert len(result.products) == 1


class TestEmployeesApiIntegration:
    @pytest.mark.asyncio
    async def test_get_offers_uses_admin_job_offers_endpoint(self, mocker):
        mocker.patch(
            "desktop_alkozon.services.api_client.load_config",
            return_value={"API_BASE_URL": "http://test:8080/api", "API_TIMEOUT": 10},
        )
        mocker.patch(
            "desktop_alkozon.services.api_client.api_client.client.request",
            new_callable=AsyncMock,
        )
        ApiClient._instance = None

        mock_response = [
            {
                "id": 1,
                "title": "Kierowca",
                "description": "Test",
                "status": "OPEN",
                "createdAt": "2024-01-01T00:00:00Z",
                "updatedAt": "2024-01-01T00:00:00Z",
            }
        ]
        desktop_alkozon.services.api_client.api_client.client.request.return_value = (
            MagicMock(
                json=MagicMock(return_value=mock_response),
                status_code=200,
                raise_for_status=MagicMock(),
            )
        )

        service = EmployeesService()
        result = await service.get_offers()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_employees_uses_admin_users_endpoint(self, mocker):
        mocker.patch(
            "desktop_alkozon.services.api_client.load_config",
            return_value={"API_BASE_URL": "http://test:8080/api", "API_TIMEOUT": 10},
        )
        mocker.patch(
            "desktop_alkozon.services.api_client.api_client.client.request",
            new_callable=AsyncMock,
        )
        ApiClient._instance = None

        mock_response = [
            {
                "id": 1,
                "email": "jan@example.com",
                "role": "EMPLOYEE",
                "active": True,
                "courier": False,
            }
        ]
        desktop_alkozon.services.api_client.api_client.client.request.return_value = (
            MagicMock(
                json=MagicMock(return_value=mock_response),
                status_code=200,
                raise_for_status=MagicMock(),
            )
        )

        service = EmployeesService()
        result = await service.get_employees()
        assert len(result) == 1


class TestDeliveriesApiIntegration:
    @pytest.mark.asyncio
    async def test_get_couriers_uses_admin_users_endpoint(self, mocker):
        mocker.patch(
            "desktop_alkozon.services.api_client.load_config",
            return_value={"API_BASE_URL": "http://test:8080/api", "API_TIMEOUT": 10},
        )
        mocker.patch(
            "desktop_alkozon.services.api_client.api_client.client.request",
            new_callable=AsyncMock,
        )
        ApiClient._instance = None

        mock_response = [
            {
                "id": 1,
                "email": "jan@example.com",
                "role": "EMPLOYEE",
                "active": True,
                "courier": True,
            }
        ]
        desktop_alkozon.services.api_client.api_client.client.request.return_value = (
            MagicMock(
                json=MagicMock(return_value=mock_response),
                status_code=200,
                raise_for_status=MagicMock(),
            )
        )

        service = DeliveriesService()
        result = await service.get_couriers()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_deliveries_uses_deliveries_endpoint(self, mocker):
        mocker.patch(
            "desktop_alkozon.services.api_client.load_config",
            return_value={"API_BASE_URL": "http://test:8080/api", "API_TIMEOUT": 10},
        )
        mocker.patch(
            "desktop_alkozon.services.api_client.api_client.client.request",
            new_callable=AsyncMock,
        )
        ApiClient._instance = None

        mock_response = [
            {
                "id": 1,
                "orderId": 100,
                "courierId": 1,
                "courierEmail": "jan@example.com",
                "status": "IN_TRANSIT",
                "addressSnapshot": "Warszawa",
            }
        ]
        desktop_alkozon.services.api_client.api_client.client.request.return_value = (
            MagicMock(
                json=MagicMock(return_value=mock_response),
                status_code=200,
                raise_for_status=MagicMock(),
            )
        )

        service = DeliveriesService()
        result = await service.get_deliveries()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_announcements_uses_announcements_endpoint(self, mocker):
        mocker.patch(
            "desktop_alkozon.services.api_client.load_config",
            return_value={"API_BASE_URL": "http://test:8080/api", "API_TIMEOUT": 10},
        )
        mocker.patch(
            "desktop_alkozon.services.api_client.api_client.client.request",
            new_callable=AsyncMock,
        )
        ApiClient._instance = None

        mock_response = [
            {
                "id": 1,
                "title": "Test",
                "content": "Content",
                "createdAt": "2024-01-01T00:00:00Z",
            }
        ]
        desktop_alkozon.services.api_client.api_client.client.request.return_value = (
            MagicMock(
                json=MagicMock(return_value=mock_response),
                status_code=200,
                raise_for_status=MagicMock(),
            )
        )

        service = DeliveriesService()
        result = await service.get_announcements()
        assert len(result) == 1


class TestApiErrorHandling:
    @pytest.mark.asyncio
    async def test_401_triggers_token_refresh(self, mocker):
        mocker.patch(
            "desktop_alkozon.services.api_client.load_config",
            return_value={"API_BASE_URL": "http://test:8080/api", "API_TIMEOUT": 10},
        )
        ApiClient._instance = None
        api_client = ApiClient()
        api_client.set_tokens("access", "refresh")

        refresh_mock = AsyncMock(
            return_value=MagicMock(
                json=MagicMock(
                    return_value={
                        "accessToken": "new_access",
                        "refreshToken": "new_refresh",
                    }
                ),
                status_code=200,
                raise_for_status=MagicMock(),
            )
        )
        api_client._refresh_access_token = refresh_mock

        request_mock = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Unauthorized", request=MagicMock(), response=MagicMock(status_code=401)
            )
        )
        api_client.client.request = request_mock

        with pytest.raises(httpx.HTTPStatusError):
            await api_client.get("/test")

    @pytest.mark.asyncio
    async def test_network_error_returns_none_for_services(self, mocker):
        mocker.patch(
            "desktop_alkozon.services.api_client.load_config",
            return_value={"API_BASE_URL": "http://test:8080/api", "API_TIMEOUT": 10},
        )
        ApiClient._instance = None
        api_client = ApiClient()
        api_client.client.request = AsyncMock(
            side_effect=httpx.NetworkError("Connection failed")
        )

        service = WarehouseService()
        result = await service.get_all_items()
        assert result is None
