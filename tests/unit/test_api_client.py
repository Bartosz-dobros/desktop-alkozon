import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from desktop_alkozon.services.api_client import ApiClient


@pytest.fixture
def api_client(mocker):
    mocker.patch("desktop_alkozon.services.api_client.load_dotenv")
    client = ApiClient()
    return client


@pytest.fixture
def mock_response():
    def _make_response(data, status_code=200):
        mock = MagicMock()
        mock.json.return_value = data
        mock.status_code = status_code
        return mock
    return _make_response


@pytest.mark.asyncio
async def test_api_client_post_success(api_client, mock_response):
    api_client.client = AsyncMock()
    api_client.client.post.return_value = mock_response({"status": "ok"})
    
    result = await api_client.post("/test", {"key": "value"})
    
    assert result == {"status": "ok"}
    api_client.client.post.assert_called_once()


@pytest.mark.asyncio
async def test_api_client_get_success(api_client, mock_response):
    api_client.client = AsyncMock()
    api_client.client.get.return_value = mock_response({"data": "test"})
    
    result = await api_client.get("/test")
    
    assert result == {"data": "test"}
    api_client.client.get.assert_called_once()


@pytest.mark.asyncio
async def test_api_client_put_success(api_client, mock_response):
    api_client.client = AsyncMock()
    api_client.client.put.return_value = mock_response({"updated": True})
    
    result = await api_client.put("/test/1", {"key": "new_value"})
    
    assert result == {"updated": True}
    api_client.client.put.assert_called_once()


@pytest.mark.asyncio
async def test_api_client_delete_success(api_client, mock_response):
    api_client.client = AsyncMock()
    api_client.client.delete.return_value = mock_response({"deleted": True})
    
    result = await api_client.delete("/test/1")
    
    assert result == {"deleted": True}
    api_client.client.delete.assert_called_once()


@pytest.mark.asyncio
async def test_api_client_get_with_auth_header(api_client, mock_response, mocker):
    mocker.patch.dict("os.environ", {"API_TOKEN": "test_token_123"})
    api_client.client = AsyncMock()
    api_client.client.get.return_value = mock_response({"data": "test"})
    
    await api_client.get("/test")
    
    call_kwargs = api_client.client.get.call_args.kwargs
    assert "Authorization" in call_kwargs.get("headers", {})
    assert call_kwargs["headers"]["Authorization"] == "Bearer test_token_123"


@pytest.mark.asyncio
async def test_api_client_post_timeout_error(api_client, mocker):
    api_client.client = AsyncMock()
    api_client.client.post.side_effect = httpx.TimeoutException("Request timed out")
    
    with pytest.raises(httpx.TimeoutException):
        await api_client.post("/test", {"key": "value"})


@pytest.mark.asyncio
async def test_api_client_get_network_error(api_client, mocker):
    api_client.client = AsyncMock()
    api_client.client.get.side_effect = httpx.NetworkError("Connection failed")
    
    with pytest.raises(httpx.NetworkError):
        await api_client.get("/test")


@pytest.mark.asyncio
async def test_api_client_http_status_error(api_client, mock_response):
    api_client.client = AsyncMock()
    error_response = MagicMock()
    error_response.status_code = 404
    error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Not found", request=MagicMock(), response=error_response
    )
    api_client.client.get.return_value = error_response
    
    with pytest.raises(httpx.HTTPStatusError):
        await api_client.get("/test")


@pytest.mark.asyncio
async def test_api_client_close(api_client):
    api_client.client = AsyncMock()
    
    await api_client.close()
    
    api_client.client.aclose.assert_called_once()


@pytest.mark.asyncio
async def test_api_client_build_url(api_client, mocker):
    mocker.patch.dict("os.environ", {"API_BASE_URL": "https://api.test.com"})
    client = api_client.__class__()
    url = client._build_url("/endpoint")
    assert url == "https://api.test.com/endpoint"
