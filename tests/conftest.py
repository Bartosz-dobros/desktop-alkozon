import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture(autouse=True)
def mock_keyring_backends(mocker):
    mocker.patch("desktop_alkozon.core.auth.keyring.get_password", return_value=None)
    mocker.patch("desktop_alkozon.core.auth.keyring.set_password")
    mocker.patch("desktop_alkozon.core.auth.keyring.delete_password")

    async def _noop_encrypt(source_path, dest_path):
        import shutil

        shutil.copy2(source_path, dest_path)

    async def _noop_decrypt(source_path, dest_path):
        import shutil

        shutil.copy2(source_path, dest_path)

    mocker.patch("desktop_alkozon.core.database.encrypt_file", _noop_encrypt)
    mocker.patch("desktop_alkozon.core.database.decrypt_file", _noop_decrypt)


@pytest.fixture
def valid_credentials():
    return {"email": "manager@example.com", "password": "Manager123!"}


@pytest.fixture
def employee_credentials():
    return {"email": "employee@example.com", "password": "Employee123!"}


@pytest.fixture
def invalid_credentials():
    return {"email": "wrong@example.com", "password": "wrongpass"}


@pytest.fixture
def two_fa_code():
    return "123456"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
