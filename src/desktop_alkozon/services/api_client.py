import httpx
from desktop_alkozon.config import load_config


class ApiClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        config = load_config()
        self.base_url = config.get("API_BASE_URL") or "http://localhost:8080/api"
        self.timeout = config.get("API_TIMEOUT", 30)
        self.client = httpx.AsyncClient(timeout=self.timeout)
        self._access_token: str | None = None
        self._refresh_token: str | None = None

    def set_tokens(self, access_token: str, refresh_token: str | None = None):
        self._access_token = access_token
        if refresh_token:
            self._refresh_token = refresh_token

    def clear_tokens(self):
        self._access_token = None
        self._refresh_token = None

    def _get_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        return headers

    async def post(self, endpoint: str, data: dict | None = None) -> dict:
        url = f"{self.base_url}{endpoint}"
        response = await self.client.post(url, json=data or {}, headers=self._get_headers())
        response.raise_for_status()
        return response.json()

    async def get(self, endpoint: str, params: dict | None = None) -> dict | list:
        url = f"{self.base_url}{endpoint}"
        response = await self.client.get(url, params=params, headers=self._get_headers())
        response.raise_for_status()
        return response.json()

    async def put(self, endpoint: str, data: dict) -> dict:
        url = f"{self.base_url}{endpoint}"
        response = await self.client.put(url, json=data, headers=self._get_headers())
        response.raise_for_status()
        return response.json()

    async def patch(self, endpoint: str, data: dict | None = None) -> dict:
        url = f"{self.base_url}{endpoint}"
        response = await self.client.patch(url, json=data or {}, headers=self._get_headers())
        response.raise_for_status()
        return response.json()

    async def delete(self, endpoint: str) -> dict:
        url = f"{self.base_url}{endpoint}"
        response = await self.client.delete(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json()

    async def close(self):
        await self.client.aclose()


api_client = ApiClient()
