import httpx
import os
from dotenv import load_dotenv

load_dotenv()

class ApiClient:
    
    def __init__(self):
        self.base_url = os.getenv("API_BASE_URL")
        self.timeout = int(os.getenv("API_TIMEOUT", 10))
        self.client = httpx.AsyncClient(timeout=self.timeout)

    def _build_url(self, endpoint: str) -> str:
        return f"{self.base_url}{endpoint}"

    def _get_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        token = os.getenv("API_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    async def post(self, endpoint: str, data: dict) -> dict:
        url = self._build_url(endpoint)
        response = await self.client.post(url, json=data, headers=self._get_headers())
        response.raise_for_status()
        return response.json()

    async def get(self, endpoint: str) -> dict:
        url = self._build_url(endpoint)
        response = await self.client.get(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json()

    async def put(self, endpoint: str, data: dict) -> dict:
        url = self._build_url(endpoint)
        response = await self.client.put(url, json=data, headers=self._get_headers())
        response.raise_for_status()
        return response.json()

    async def delete(self, endpoint: str) -> dict:
        url = self._build_url(endpoint)
        response = await self.client.delete(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json()

    async def close(self):
        await self.client.aclose()