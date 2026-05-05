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
        self._refresh_in_progress = False

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

    async def _refresh_access_token(self) -> bool:
        if self._refresh_in_progress or not self._refresh_token:
            return False
        self._refresh_in_progress = True
        try:
            response = await self.client.post(
                f"{self.base_url}/auth/refresh",
                json={"refreshToken": self._refresh_token},
            )
            response.raise_for_status()
            data = response.json()
            self._access_token = data.get("accessToken")
            new_refresh = data.get("refreshToken")
            if new_refresh:
                self._refresh_token = new_refresh
            return True
        except Exception:
            self.clear_tokens()
            return False
        finally:
            self._refresh_in_progress = False

    async def _request(self, method: str, endpoint: str, **kwargs):
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        kwargs["headers"] = {**headers, **kwargs.get("headers", {})}

        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if (
                e.response.status_code == 401
                and self._refresh_token
                and await self._refresh_access_token()
            ):
                kwargs["headers"]["Authorization"] = f"Bearer {self._access_token}"
                response = await self.client.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
            raise

    async def post(self, endpoint: str, data: dict | None = None) -> dict:
        return await self._request("POST", endpoint, json=data or {})

    async def get(self, endpoint: str, params: dict | None = None) -> dict | list:
        return await self._request("GET", endpoint, params=params)

    async def put(self, endpoint: str, data: dict) -> dict:
        return await self._request("PUT", endpoint, json=data)

    async def patch(self, endpoint: str, data: dict | None = None) -> dict:
        return await self._request("PATCH", endpoint, json=data or {})

    async def delete(self, endpoint: str) -> dict:
        return await self._request("DELETE", endpoint)

    async def close(self):
        await self.client.aclose()


api_client = ApiClient()
