import tempfile
from pathlib import Path
from unittest.mock import AsyncMock

import httpx
import pytest

from desktop_alkozon.core.database import init_db, set_db_path
from desktop_alkozon.core.outbox import enqueue, get_by_id
from desktop_alkozon.core.repository import get_all_users, get_sync_status
from desktop_alkozon.core.sync_manager import sync_manager


@pytest.fixture
def db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    set_db_path(path)
    yield path
    Path(path).unlink(missing_ok=True)
    set_db_path(None)


@pytest.fixture
async def initialized_db(db_path):
    await init_db(db_path)
    return db_path


def reset_sync_manager():
    sync_manager._syncing = False
    sync_manager._listeners = {
        "sync_start": [],
        "sync_progress": [],
        "sync_complete": [],
    }


class TestSyncManagerEvents:
    def test_on_off_events(self):
        reset_sync_manager()
        calls = []

        def handler(*args, **kwargs):
            calls.append(("called", args, kwargs))

        sync_manager.on("sync_complete", handler)
        sync_manager._emit("sync_complete", "done")
        assert len(calls) == 1

        sync_manager.off("sync_complete", handler)
        sync_manager._emit("sync_complete", "done")
        assert len(calls) == 1

    def test_is_syncing(self):
        reset_sync_manager()
        assert sync_manager.is_syncing() is False
        sync_manager._syncing = True
        assert sync_manager.is_syncing() is True
        sync_manager._syncing = False


@pytest.mark.asyncio
class TestSyncManagerFullSync:
    async def test_full_sync_skips_when_already_syncing(self, initialized_db, mocker):
        reset_sync_manager()
        sync_manager._syncing = True
        api_mock = mocker.patch(
            "desktop_alkozon.core.sync_manager.api_client.get",
            new_callable=AsyncMock,
        )
        await sync_manager.full_sync()
        api_mock.assert_not_called()
        sync_manager._syncing = False

    async def test_full_sync_stores_users(self, initialized_db, mocker):
        reset_sync_manager()
        mock_users = [
            {
                "id": 1,
                "email": "a@test.com",
                "role": "MANAGER",
                "active": True,
                "courier": False,
            },
            {
                "id": 2,
                "email": "b@test.com",
                "role": "EMPLOYEE",
                "active": True,
                "courier": True,
            },
        ]
        mocker.patch(
            "desktop_alkozon.core.sync_manager.api_client.get",
            new_callable=AsyncMock,
            side_effect=[
                mock_users,
                [],
                {"products": [], "rawMaterials": []},
                [],
                [],
                [],
            ],
        )
        await sync_manager.full_sync()
        users = await get_all_users(initialized_db)
        assert len(users) == 2
        status = await get_sync_status("users", initialized_db)
        assert status["status"] == "synced"

    async def test_full_sync_handles_api_error(self, initialized_db, mocker):
        reset_sync_manager()
        mocker.patch(
            "desktop_alkozon.core.sync_manager.api_client.get",
            new_callable=AsyncMock,
            side_effect=httpx.ConnectError("No connection"),
        )
        await sync_manager.full_sync()
        users = await get_all_users(initialized_db)
        assert len(users) == 0

    async def test_full_sync_emits_events(self, initialized_db, mocker):
        reset_sync_manager()
        mocker.patch(
            "desktop_alkozon.core.sync_manager.api_client.get",
            new_callable=AsyncMock,
            return_value=[],
        )
        events = []
        sync_manager.on("sync_complete", lambda p: events.append(("complete", p.phase)))
        sync_manager.on("sync_start", lambda p: events.append(("start", p.phase)))
        await sync_manager.full_sync()
        assert any(e[0] == "start" for e in events)
        assert any(e[0] == "complete" for e in events)

    async def test_full_sync_inventory(self, initialized_db, mocker):
        reset_sync_manager()
        inv_response = {
            "products": [
                {"productId": 1, "name": "Beer", "quantity": 50, "warehouseZone": "A1"},
            ],
            "rawMaterials": [
                {"id": 1, "name": "Hops", "unit": "kg", "quantity": 100.0},
            ],
        }
        mocker.patch(
            "desktop_alkozon.core.sync_manager.api_client.get",
            new_callable=AsyncMock,
            side_effect=[
                [],
                [],
                inv_response,
                [],
                [],
                [],
            ],
        )
        await sync_manager.full_sync()


@pytest.mark.asyncio
class TestSyncManagerOutbox:
    async def test_process_outbox_success(self, initialized_db, mocker):
        reset_sync_manager()
        entry = await enqueue(
            entity_type="delivery",
            http_method="PATCH",
            endpoint="/deliveries/1/status",
            entity_id="1",
            request_body={"status": "IN_TRANSIT"},
            db_path=initialized_db,
        )
        mocker.patch(
            "desktop_alkozon.core.sync_manager.api_client._request",
            new_callable=AsyncMock,
            return_value={"id": 1, "status": "IN_TRANSIT"},
        )
        mocker.patch(
            "desktop_alkozon.core.sync_manager.api_client.get",
            new_callable=AsyncMock,
            return_value=[],
        )
        await sync_manager.process_outbox()
        updated = await get_by_id(entry.id, initialized_db)
        assert updated.status == "completed"

    async def test_process_outbox_http_error(self, initialized_db, mocker):
        reset_sync_manager()
        entry = await enqueue(
            entity_type="delivery",
            http_method="PATCH",
            endpoint="/deliveries/1/status",
            entity_id="1",
            request_body={"status": "IN_TRANSIT"},
            db_path=initialized_db,
        )
        error_response = httpx.Response(409, request=httpx.Request("PATCH", "/test"))
        mocker.patch(
            "desktop_alkozon.core.sync_manager.api_client._request",
            new_callable=AsyncMock,
            side_effect=httpx.HTTPStatusError(
                "Conflict",
                request=httpx.Request("PATCH", "/test"),
                response=error_response,
            ),
        )
        mocker.patch(
            "desktop_alkozon.core.sync_manager.api_client.get",
            new_callable=AsyncMock,
            return_value=[],
        )
        await sync_manager.process_outbox()
        updated = await get_by_id(entry.id, initialized_db)
        assert updated.status == "failed"

    async def test_process_outbox_connection_lost(self, initialized_db, mocker):
        reset_sync_manager()
        entry = await enqueue(
            entity_type="test",
            http_method="POST",
            endpoint="/test",
            db_path=initialized_db,
        )
        mocker.patch(
            "desktop_alkozon.core.sync_manager.api_client._request",
            new_callable=AsyncMock,
            side_effect=httpx.ConnectError("No connection"),
        )
        await sync_manager.process_outbox()
        updated = await get_by_id(entry.id, initialized_db)
        assert updated.status == "pending"

    async def test_process_outbox_offline_error(self, initialized_db, mocker):
        from desktop_alkozon.core.exceptions import OfflineError

        reset_sync_manager()
        entry = await enqueue(
            entity_type="test",
            http_method="POST",
            endpoint="/test",
            db_path=initialized_db,
        )
        mocker.patch(
            "desktop_alkozon.core.sync_manager.api_client._request",
            new_callable=AsyncMock,
            side_effect=OfflineError("No connection"),
        )
        await sync_manager.process_outbox()
        updated = await get_by_id(entry.id, initialized_db)
        assert updated.status == "pending"

    async def test_process_outbox_emits_events(self, initialized_db, mocker):
        reset_sync_manager()
        await enqueue("test", "POST", "/test", entity_id="1", db_path=initialized_db)
        mocker.patch(
            "desktop_alkozon.core.sync_manager.api_client._request",
            new_callable=AsyncMock,
            return_value={"ok": True},
        )
        mocker.patch(
            "desktop_alkozon.core.sync_manager.api_client.get",
            new_callable=AsyncMock,
            return_value=[],
        )
        events = []
        sync_manager.on(
            "sync_complete", lambda p, r=None: events.append(("complete", p.phase))
        )
        sync_manager.on("sync_start", lambda p: events.append(("start", p.phase)))
        await sync_manager.process_outbox()
        assert any(e[0] == "start" for e in events)
        assert any(e[0] == "complete" for e in events)

    async def test_process_empty_outbox(self, initialized_db, mocker):
        reset_sync_manager()
        api_mock = mocker.patch(
            "desktop_alkozon.core.sync_manager.api_client._request",
            new_callable=AsyncMock,
        )
        await sync_manager.process_outbox()
        api_mock.assert_not_called()

    async def test_process_outbox_create_employee_success(self, initialized_db, mocker):
        reset_sync_manager()
        import base64
        import json as pyjson

        header = (
            base64.urlsafe_b64encode(pyjson.dumps({"alg": "HS256"}).encode())
            .rstrip(b"=")
            .decode()
        )
        payload = (
            base64.urlsafe_b64encode(
                pyjson.dumps(
                    {"sub": 123, "email": "novy@test.com", "role": "CUSTOMER"}
                ).encode()
            )
            .rstrip(b"=")
            .decode()
        )
        fake_access_token = f"{header}.{payload}.fakesig"
        mock_register_response = {
            "accessToken": fake_access_token,
            "refreshToken": "fake_refresh",
            "tokenType": "Bearer",
            "expiresInSeconds": 3600,
        }
        mock_update_response = {
            "id": 123,
            "email": "novy@test.com",
            "role": "MANAGER",
            "active": True,
            "courier": True,
        }

        entry = await enqueue(
            entity_type="create_employee",
            http_method="POST",
            endpoint="/auth/register",
            entity_id=None,
            request_body={
                "register": {
                    "email": "novy@test.com",
                    "password": "StrongPass1!",
                    "firstName": "Jan",
                    "lastName": "Kowalski",
                    "ageConfirmed": True,
                    "adultConfirmed": True,
                },
                "update": {
                    "role": "MANAGER",
                    "active": True,
                    "courier": True,
                },
            },
            db_path=initialized_db,
        )

        mocker.patch(
            "desktop_alkozon.core.sync_manager.api_client._request",
            new_callable=AsyncMock,
            side_effect=[mock_register_response, mock_update_response],
        )
        mocker.patch(
            "desktop_alkozon.core.sync_manager.api_client.get",
            new_callable=AsyncMock,
            return_value=[],
        )

        await sync_manager.process_outbox()

        updated = await get_by_id(entry.id, initialized_db)
        assert updated.status == "completed"

    async def test_process_outbox_create_employee_register_fails(
        self, initialized_db, mocker
    ):
        reset_sync_manager()
        entry = await enqueue(
            entity_type="create_employee",
            http_method="POST",
            endpoint="/auth/register",
            entity_id=None,
            request_body={
                "register": {"email": "novy@test.com", "password": "StrongPass1!"},
                "update": {"role": "EMPLOYEE", "active": True, "courier": False},
            },
            db_path=initialized_db,
        )

        error_response = httpx.Response(
            409, request=httpx.Request("POST", "/auth/register")
        )
        mocker.patch(
            "desktop_alkozon.core.sync_manager.api_client._request",
            new_callable=AsyncMock,
            side_effect=httpx.HTTPStatusError(
                "Conflict",
                request=httpx.Request("POST", "/auth/register"),
                response=error_response,
            ),
        )
        mocker.patch(
            "desktop_alkozon.core.sync_manager.api_client.get",
            new_callable=AsyncMock,
            return_value=[],
        )

        await sync_manager.process_outbox()

        updated = await get_by_id(entry.id, initialized_db)
        assert updated.status == "failed"

    async def test_process_outbox_skips_when_syncing(self, initialized_db, mocker):
        reset_sync_manager()
        sync_manager._syncing = True
        api_mock = mocker.patch(
            "desktop_alkozon.core.sync_manager.api_client._request",
            new_callable=AsyncMock,
        )
        await sync_manager.process_outbox()
        api_mock.assert_not_called()
        sync_manager._syncing = False
