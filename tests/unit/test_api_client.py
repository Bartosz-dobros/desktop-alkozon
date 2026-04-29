import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock
from desktop_alkozon.services.api_client import ApiClient


@pytest.fixture
def api_client(mocker):
    mocker.patch("desktop_alkozon.services.api_client.load_config", return_value={
        "API_BASE_URL": "http://test:8080/api",
        "API_TIMEOUT": 10
    })
    ApiClient._instance = None
    client = ApiClient()
    return client


@pytest.fixture
def mock_response():
    def _make_response(data, status_code=200):
        mock = MagicMock()
        mock.json.return_value = data
        mock.status_code = status_code
        mock.raise_for_status = MagicMock()
        return mock
    return _make_response


class TestApiClientSingleton:
    def test_singleton_pattern(self):
        ApiClient._instance = None
        client1 = ApiClient()
        client2 = ApiClient()
        assert client1 is client2


class TestApiClientTokens:
    def test_set_tokens(self, api_client):
        api_client.set_tokens("access_123", "refresh_456")
        assert api_client._access_token == "access_123"
        assert api_client._refresh_token == "refresh_456"

    def test_clear_tokens(self, api_client):
        api_client.set_tokens("access_123", "refresh_456")
        api_client.clear_tokens()
        assert api_client._access_token is None
        assert api_client._refresh_token is None


class TestApiClientHeaders:
    def test_headers_without_token(self, api_client):
        api_client.clear_tokens()
        headers = api_client._get_headers()
        assert "Content-Type" in headers
        assert "Authorization" not in headers

    def test_headers_with_token(self, api_client):
        api_client.set_tokens("test_token")
        headers = api_client._get_headers()
        assert headers["Authorization"] == "Bearer test_token"


@pytest.mark.asyncio
class TestApiClientRequests:
    async def test_post_success(self, api_client, mock_response):
        api_client.client = AsyncMock()
        api_client.client.post.return_value = mock_response({"status": "ok"})
        
        result = await api_client.post("/test", {"key": "value"})
        
        assert result == {"status": "ok"}
        api_client.client.post.assert_called_once()

    async def test_get_success(self, api_client, mock_response):
        api_client.client = AsyncMock()
        api_client.client.get.return_value = mock_response({"data": "test"})
        
        result = await api_client.get("/test")
        
        assert result == {"data": "test"}

    async def test_put_success(self, api_client, mock_response):
        api_client.client = AsyncMock()
        api_client.client.put.return_value = mock_response({"updated": True})
        
        result = await api_client.put("/test/1", {"key": "new_value"})
        
        assert result == {"updated": True}

    async def test_delete_success(self, api_client, mock_response):
        api_client.client = AsyncMock()
        api_client.client.delete.return_value = mock_response({"deleted": True})
        
        result = await api_client.delete("/test/1")
        
        assert result == {"deleted": True}

    async def test_patch_success(self, api_client, mock_response):
        api_client.client = AsyncMock()
        api_client.client.patch.return_value = mock_response({"status": "updated"})
        
        result = await api_client.patch("/test/1", {"status": "active"})
        
        assert result == {"status": "updated"}

    async def test_get_with_params(self, api_client, mock_response):
        api_client.client = AsyncMock()
        api_client.client.get.return_value = mock_response([{"id": 1}])
        
        result = await api_client.get("/test", params={"status": "active"})
        
        assert len(result) == 1

    async def test_post_timeout_error(self, api_client):
        api_client.client = AsyncMock()
        api_client.client.post.side_effect = httpx.TimeoutException("Request timed out")
        
        with pytest.raises(httpx.TimeoutException):
            await api_client.post("/test", {"key": "value"})

    async def test_get_network_error(self, api_client):
        api_client.client = AsyncMock()
        api_client.client.get.side_effect = httpx.NetworkError("Connection failed")
        
        with pytest.raises(httpx.NetworkError):
            await api_client.get("/test")

    async def test_http_status_error(self, api_client, mock_response):
        api_client.client = AsyncMock()
        error_response = MagicMock()
        error_response.status_code = 404
        error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not found", request=MagicMock(), response=error_response
        )
        api_client.client.get.return_value = error_response
        
        with pytest.raises(httpx.HTTPStatusError):
            await api_client.get("/test")

    async def test_close(self, api_client):
        api_client.client = AsyncMock()
        
        await api_client.close()
        
        api_client.client.aclose.assert_called_once()
