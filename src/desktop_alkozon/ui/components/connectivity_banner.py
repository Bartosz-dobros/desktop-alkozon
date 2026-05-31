import contextlib

import flet as ft

from desktop_alkozon.core.connectivity import connectivity_service
from desktop_alkozon.core.i18n import i18n
from desktop_alkozon.core.sync_manager import sync_manager


def create_connectivity_banner(page: ft.Page) -> ft.Container:
    text_widget = ft.Text(
        i18n.t("offline.banner_online"),
        size=12,
        color=ft.Colors.WHITE,
        weight=ft.FontWeight.BOLD,
    )
    banner = ft.Container(
        content=text_widget,
        bgcolor=ft.Colors.GREEN_700,
        padding=ft.padding.symmetric(vertical=4, horizontal=16),
        visible=False,
        animate_opacity=300,
    )

    has_pending = [False]

    def update_banner(online: bool | None = None, _=None):
        if online is None:
            online = connectivity_service.is_online()
        if sync_manager.is_syncing():
            text_widget.value = i18n.t("offline.banner_syncing")
            banner.bgcolor = ft.Colors.BLUE_700
            banner.visible = True
        elif not online:
            text_widget.value = i18n.t("offline.banner_offline")
            banner.bgcolor = ft.Colors.ORANGE_800
            banner.visible = True
        else:
            banner.visible = False
        with contextlib.suppress(Exception):
            page.update()

    def on_online():
        update_banner(True)
        has_pending[0] = True

    def on_offline():
        update_banner(False)

    def on_sync_complete(progress, results=None):
        has_pending[0] = False
        if results:
            success = sum(1 for r in results if r.status == "success")
            failed = sum(1 for r in results if r.status == "failed")
            if failed > 0:
                page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(
                            i18n.t(
                                "offline.sync_result", success=success, failed=failed
                            ),
                            weight=ft.FontWeight.BOLD,
                        ),
                        bgcolor=ft.Colors.AMBER_700,
                    )
                )
            elif success > 0:
                page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(
                            i18n.t("offline.sync_success", success=success),
                            weight=ft.FontWeight.BOLD,
                        ),
                        bgcolor=ft.Colors.GREEN_700,
                    )
                )
        update_banner()

    connectivity_service.on("online", on_online)
    connectivity_service.on("offline", on_offline)
    connectivity_service.on("change", update_banner)
    sync_manager.on("sync_complete", on_sync_complete)
    sync_manager.on("sync_start", lambda p: update_banner())

    if not connectivity_service.is_online():
        on_offline()

    return banner
