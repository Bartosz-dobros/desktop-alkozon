import pytest
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def valid_credentials():
    return {"username": "admin", "password": "password123"}


@pytest.fixture
def invalid_credentials():
    return {"username": "wrong", "password": "wrongpass"}


@pytest.fixture
def two_fa_code():
    return "123456"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
