import asyncio
from collections.abc import Callable

from desktop_alkozon.services.api_client import api_client


class ConnectivityService:
    CHECK_INTERVAL = 30

    def __init__(self):
        self._online = False
        self._running = False
        self._task: asyncio.Task | None = None
        self._listeners: dict[str, list[Callable]] = {
            "online": [],
            "offline": [],
            "change": [],
        }

    def is_online(self) -> bool:
        return self._online

    def on(self, event: str, callback: Callable):
        if event in self._listeners:
            self._listeners[event].append(callback)

    def off(self, event: str, callback: Callable):
        if event in self._listeners and callback in self._listeners[event]:
            self._listeners[event].remove(callback)

    def _emit(self, event: str, *args, **kwargs):
        for cb in self._listeners.get(event, []):
            try:
                result = cb(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    task = asyncio.create_task(result)
                    self._background_tasks = getattr(self, "_background_tasks", set())
                    self._background_tasks.add(task)
                    task.add_done_callback(self._background_tasks.discard)
            except Exception as e:
                print(f"Connectivity listener error: {e}")

    def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._ping_loop())

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None

    async def _ping_loop(self):
        while self._running:
            try:
                online = await api_client.health_check()
                if online and not self._online:
                    self._online = True
                    self._emit("online")
                    self._emit("change", True)
                elif not online and self._online:
                    self._online = False
                    self._emit("offline")
                    self._emit("change", False)
            except Exception as e:
                print(f"Connectivity ping error: {e}")

            await asyncio.sleep(self.CHECK_INTERVAL)


connectivity_service = ConnectivityService()
