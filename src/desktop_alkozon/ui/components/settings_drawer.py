from contextlib import suppress

import flet as ft

from desktop_alkozon.core.i18n import i18n, save_language

THEME_KEY = "alkozon_theme_mode"


async def _load_theme(page: ft.Page) -> ft.ThemeMode:
    try:
        value = await page.shared_preferences.get(THEME_KEY)
        if value == "light":
            return ft.ThemeMode.LIGHT
    except Exception:
        pass
    return ft.ThemeMode.DARK


async def _save_theme(page: ft.Page, mode: ft.ThemeMode) -> None:
    with suppress(Exception):
        await page.shared_preferences.set(
            THEME_KEY, "light" if mode == ft.ThemeMode.LIGHT else "dark"
        )


def _rebuild_current_view(page: ft.Page) -> None:
    factory = getattr(page, "_rebuild_view", None)
    if factory:
        page.clean()
        page.add(factory())
        page.update()


def setup_theme(page: ft.Page) -> None:
    async def load_and_apply():
        mode = await _load_theme(page)
        page.theme_mode = mode
        page.drawer = make_settings_drawer(page)
        page.update()

    page.run_task(load_and_apply)


def make_settings_drawer(page: ft.Page) -> ft.NavigationDrawer:
    current_mode = page.theme_mode
    is_dark = current_mode == ft.ThemeMode.DARK
    is_pl = i18n.is_polish

    async def on_theme_toggle(e: ft.ControlEvent) -> None:
        is_dark = e.control.value
        new_mode = ft.ThemeMode.DARK if is_dark else ft.ThemeMode.LIGHT
        page.theme_mode = new_mode
        await _save_theme(page, new_mode)
        await page.close_drawer()
        page.update()

    theme_switch = ft.Switch(
        value=is_dark,
        on_change=on_theme_toggle,
    )

    async def on_language_toggle(e: ft.ControlEvent) -> None:
        new_lang = "pl" if e.control.value else "en"
        i18n.current_lang = new_lang
        await save_language(page, new_lang)
        await page.close_drawer()
        snack = ft.SnackBar(
            content=ft.Text(i18n.t("settings.language_changed")),
            duration=1500,
            bgcolor=ft.Colors.GREEN_800,
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()
        _rebuild_current_view(page)

    lang_switch = ft.Switch(
        value=is_pl,
        on_change=on_language_toggle,
    )

    drawer = ft.NavigationDrawer(
        controls=[
            ft.Container(
                padding=ft.Padding.all(20),
                content=ft.Column(
                    controls=[
                        ft.Text(
                            i18n.t("settings.title"),
                            size=22,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Divider(height=20),
                        ft.Text(
                            i18n.t("settings.theme"),
                            size=14,
                            color=ft.Colors.GREY_400,
                        ),
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.DARK_MODE, size=22),
                                theme_switch,
                                ft.Icon(ft.Icons.LIGHT_MODE, size=22),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        ft.Divider(height=10),
                        ft.Text(
                            i18n.t("settings.language"),
                            size=14,
                            color=ft.Colors.GREY_400,
                        ),
                        ft.Row(
                            controls=[
                                ft.Text("EN", size=14, weight=ft.FontWeight.BOLD),
                                lang_switch,
                                ft.Text("PL", size=14, weight=ft.FontWeight.BOLD),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                    ],
                ),
            ),
        ],
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
    )

    return drawer


def make_hamburger_button(page: ft.Page) -> ft.IconButton:
    return ft.IconButton(
        icon=ft.Icons.MENU,
        icon_size=28,
        tooltip=i18n.t("settings.title"),
        on_click=lambda e: page.run_task(page.show_drawer),
    )
