import json
from collections.abc import Callable
from dataclasses import dataclass

import httpx

from desktop_alkozon.core import repository
from desktop_alkozon.core.auth import auth_service
from desktop_alkozon.core.connectivity import connectivity_service
from desktop_alkozon.core.database import get_db_path
from desktop_alkozon.core.outbox import (
    get_pending,
    mark_completed,
    mark_failed,
    mark_in_progress,
)
from desktop_alkozon.services.api_client import api_client

SYNC_SOURCES = [
    "users",
    "job_offers",
    "inventory",
    "deliveries",
    "replenishments",
    "announcements",
]


@dataclass
class SyncResult:
    outbox_id: str
    status: str
    error_message: str | None = None


@dataclass
class SyncProgress:
    phase: str = ""
    current: int = 0
    total: int = 0
    message: str = ""


class SyncManager:
    def __init__(self):
        self._syncing = False
        self._listeners: dict[str, list[Callable]] = {
            "sync_start": [],
            "sync_progress": [],
            "sync_complete": [],
        }

    def on(self, event: str, callback: Callable):
        if event in self._listeners:
            self._listeners[event].append(callback)

    def off(self, event: str, callback: Callable):
        if event in self._listeners and callback in self._listeners[event]:
            self._listeners[event].remove(callback)

    def _emit(self, event: str, *args, **kwargs):
        for cb in self._listeners.get(event, []):
            try:
                cb(*args, **kwargs)
            except Exception as e:
                print(f"SyncManager listener error: {e}")

    def is_syncing(self) -> bool:
        return self._syncing

    async def full_sync(self):
        if self._syncing:
            return
        self._syncing = True
        db_path = get_db_path()
        self._emit(
            "sync_start", SyncProgress(phase="full_sync", message="Starting full sync")
        )

        sources = [
            ("users", "/admin/users", repository.upsert_users),
            ("job_offers", "/admin/job-offers", repository.upsert_job_offers),
            ("inventory_full", "/inventory", self._upsert_inventory_full),
            ("deliveries", "/deliveries", repository.upsert_deliveries),
            (
                "replenishments",
                "/warehouse/replenishment",
                repository.upsert_replenishments,
            ),
            (
                "announcements",
                "/admin/delivery-announcements",
                repository.upsert_announcements,
            ),
        ]

        for idx, (name, endpoint, upsert_fn) in enumerate(sources):
            self._emit(
                "sync_progress",
                SyncProgress(
                    phase="full_sync",
                    current=idx,
                    total=len(sources),
                    message=f"Syncing {name}...",
                ),
            )
            try:
                response = await api_client.get(endpoint)
                if isinstance(response, list):
                    await upsert_fn(response, db_path)
                elif isinstance(response, dict) and name == "inventory_full":
                    await self._upsert_inventory_full(response, db_path)
                await repository.set_sync_status(name, "synced", db_path)
            except (httpx.ConnectError, httpx.TimeoutException):
                await repository.set_sync_status(name, "pending", db_path)
            except Exception as e:
                print(f"[Sync] {name} failed: {e}")
                await repository.set_sync_status(name, "pending", db_path)

        self._syncing = False
        self._emit(
            "sync_complete",
            SyncProgress(phase="full_sync", message="Full sync complete"),
        )

    async def _upsert_inventory_full(self, response: dict, db_path: str):
        products = response.get("products", [])
        raw_materials = response.get("rawMaterials", [])
        await repository.upsert_inventory(products, raw_materials, db_path)

    async def process_outbox(self):
        if self._syncing:
            return
        self._syncing = True
        db_path = get_db_path()
        entries = await get_pending(db_path)
        results: list[SyncResult] = []

        self._emit(
            "sync_start",
            SyncProgress(
                phase="outbox",
                total=len(entries),
                message=f"Processing {len(entries)} pending changes",
            ),
        )

        for idx, entry in enumerate(entries):
            self._emit(
                "sync_progress",
                SyncProgress(
                    phase="outbox",
                    current=idx,
                    total=len(entries),
                    message=f"Sending {entry.http_method} {entry.endpoint}...",
                ),
            )
            await mark_in_progress(entry.id, db_path)

            try:
                body = json.loads(entry.request_body) if entry.request_body else {}
                response = await api_client._request(
                    entry.http_method, entry.endpoint, json=body
                )
                await mark_completed(
                    entry.id, json.dumps(response) if response else "{}", db_path
                )
                results.append(SyncResult(entry.id, "success"))
            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
                await mark_failed(entry.id, error_msg, db_path)
                results.append(SyncResult(entry.id, "failed", error_msg))
                await self._refresh_entity_from_api(entry, db_path)
            except (httpx.ConnectError, httpx.TimeoutException):
                await mark_failed(entry.id, "Connection lost during sync", db_path)
                results.append(SyncResult(entry.id, "connection_lost"))
            except Exception as e:
                error_msg = f"{type(e).__name__}: {e}"
                await mark_failed(entry.id, error_msg, db_path)
                results.append(SyncResult(entry.id, "failed", error_msg))

        self._syncing = False
        self._emit(
            "sync_complete",
            SyncProgress(phase="outbox", message="Outbox processing complete"),
            results,
        )

        if any(r.status == "success" for r in results):
            await self.full_sync()

    async def _refresh_entity_from_api(self, entry, db_path: str):
        try:
            if entry.entity_type == "user" and entry.entity_id:
                user = await api_client.get("/admin/users")
                if isinstance(user, list):
                    await repository.upsert_users(user, db_path)
            elif entry.entity_type == "delivery" and entry.entity_id:
                delivery = await api_client.get("/deliveries")
                if isinstance(delivery, list):
                    await repository.upsert_deliveries(delivery, db_path)
            elif entry.entity_type == "inventory":
                inventory = await api_client.get("/inventory")
                if isinstance(inventory, dict):
                    await self._upsert_inventory_full(inventory, db_path)
            elif entry.entity_type == "job_offer" and entry.entity_id:
                offers = await api_client.get("/admin/job-offers")
                if isinstance(offers, list):
                    await repository.upsert_job_offers(offers, db_path)
        except Exception:
            pass

    async def start(self):
        connectivity_service.on("online", self._on_connectivity_online)

    async def stop(self):
        connectivity_service.off("online", self._on_connectivity_online)

    async def _on_connectivity_online(self):
        if self._syncing:
            return
        if auth_service.is_offline_session():
            refreshed = await auth_service.refresh_token()
            if not refreshed:
                print(
                    "[Sync] Cannot sync — no valid tokens. User must re-authenticate."
                )
                return
            print("[Sync] Token refreshed for offline session")
        elif not api_client._access_token:
            stored_refresh = await auth_service.refresh_token()
            if not stored_refresh:
                print(
                    "[Sync] No access token available. Sync will fail for protected endpoints."
                )
        await self.process_outbox()


sync_manager = SyncManager()
