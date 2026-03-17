import httpx
import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

class ApiClient:
    
    def __init__(self):
        self.base_url = os.getenv("API_BASE_URL")
        self.timeout = int(os.getenv("API_TIMEOUT", 10))
        self.client = httpx.AsyncClient(timeout=self.timeout)

    async def post(self, endpoint: str, data: dict) -> dict:
        url = f"{self.base_url}{endpoint}"
        response = await self.client.post(url, json=data)
        response.raise_for_status()
        return response.json()

    async def get(self, endpoint: str) -> dict:
        url = f"{self.base_url}{endpoint}"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()

    async def close(self):
        await self.client.aclose()