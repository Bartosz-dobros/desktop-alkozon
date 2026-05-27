import asyncio

import flet as ft

from desktop_alkozon.config import is_demo_mode_enabled
from desktop_alkozon.core.auth import auth_service
from desktop_alkozon.core.i18n import i18n
from desktop_alkozon.ui.components.settings_drawer import (
    make_hamburger_button,
    make_settings_drawer,
    setup_theme,
)


def create_login_page_view(page: ft.Page) -> ft.Container:
    page._rebuild_view = lambda: create_login_page_view(page)

    setup_theme(page)
    page.drawer = make_settings_drawer(page)

    loading = [False]
    verification_required = [False]
    challenge_id = [None]

    username_field = ft.TextField(
        label=i18n.t("login.username"),
        width=400,
        border_radius=8,
        prefix_icon=ft.Icons.PERSON,
        max_length=50,
        text_size=16,
    )
    password_field = ft.TextField(
        label=i18n.t("login.password"),
        password=True,
        can_reveal_password=True,
        width=400,
        border_radius=8,
        prefix_icon=ft.Icons.LOCK,
        max_length=128,
        text_size=16,
    )
    verification_field = ft.TextField(
        label=i18n.t("login.verification_code"),
        width=400,
        border_radius=8,
        visible=False,
        max_length=6,
        input_filter=ft.InputFilter(allow=True, regex_string=r"^[0-9]*$"),
        keyboard_type=ft.KeyboardType.NUMBER,
        text_size=16,
    )
    login_button = ft.ElevatedButton(
        content=ft.Text(i18n.t("login.button")),
        width=400,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
    )
    status_text = ft.Text("", color=ft.Colors.RED, size=14, visible=False)

    async def login_clicked(e):
        if loading[0]:
            return

        loading[0] = True
        login_button.disabled = True
        login_button.content = ft.Text(i18n.t("login.logging_in"))
        status_text.visible = False
        page.update()

        if not verification_required[0]:
            success = await auth_service.login(
                username_field.value or "",
                password_field.value or "",
            )

            if not success and auth_service.get_pending_challenge():
                verification_required[0] = True
                challenge_id[0] = auth_service.get_pending_challenge()
                verification_field.visible = True
                loading[0] = False
                login_button.disabled = False
                login_button.content = ft.Text(i18n.t("login.enter_code"))
                status_text.value = i18n.t("login.verification_sent")
                status_text.visible = True
                page.update()
                return

            if success:
                loading[0] = False
                page.clean()
                page.add(create_main_menu_view(page))
                page.update()
                return

        if verification_required[0]:
            success = await auth_service.verify_staff_login(
                challenge_id[0] or "",
                verification_field.value or "",
            )

            if success:
                loading[0] = False
                verification_required[0] = False
                challenge_id[0] = None
                page.clean()
                page.add(create_main_menu_view(page))
                page.update()
                return

        loading[0] = False
        login_button.disabled = False
        login_button.content = ft.Text(i18n.t("login.button"))
        if auth_service.is_api_unavailable():
            status_text.value = i18n.t("login.connection_error")
            status_text.visible = True
        elif auth_service.is_locked():
            status_text.value = i18n.t("login.account_locked")
            status_text.visible = True
            login_button.disabled = True
        else:
            remaining = max(0, 5 - auth_service.attempts)
            status_text.value = i18n.t("login.invalid_credentials", remaining=remaining)
            status_text.visible = True

        page.update()

    async def enter_demo_mode(page):
        auth_service.enable_demo_mode()
        page.clean()
        page.add(create_main_menu_view(page))
        page.update()

    login_button.on_click = login_clicked

    inner_controls = [
        ft.Text("AlkozOn Desktop", size=32, weight=ft.FontWeight.BOLD),
        ft.Text(i18n.t("login.subtitle"), size=16),
        ft.Divider(),
        username_field,
        password_field,
        verification_field,
        status_text,
        login_button,
        ft.TextButton(
            i18n.t("login.forgot_password"),
            on_click=lambda e: show_password_reset_dialog(page),
        ),
    ]

    if is_demo_mode_enabled():
        inner_controls.append(
            ft.ElevatedButton(
                i18n.t("login.demo_mode"),
                width=400,
                on_click=lambda e: page.run_task(enter_demo_mode, page),
                style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE),
            )
        )

    return ft.Stack(
        controls=[
            ft.Container(
                expand=True,
                padding=40,
                alignment=ft.Alignment(0.5, 0.5),
                content=ft.Column(
                    controls=inner_controls,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                    scroll=ft.ScrollMode.AUTO,
                ),
            ),
            ft.Container(
                content=make_hamburger_button(page),
                left=12,
                top=12,
            ),
        ],
        expand=True,
    )


def show_password_reset_dialog(page: ft.Page):
    email_field = ft.TextField(
        label=i18n.t("password_reset.email_label"),
        width=400,
        border_radius=8,
        prefix_icon=ft.Icons.EMAIL,
        max_length=255,
        text_size=16,
    )
    status_text = ft.Text("", size=14, visible=False)
    send_btn = ft.ElevatedButton(
        content=ft.Text(i18n.t("password_reset.send")),
        width=400,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
    )

    async def send_clicked(e):
        email = (email_field.value or "").strip()
        if not email:
            status_text.value = i18n.t("password_reset.email_required")
            status_text.color = ft.Colors.RED
            status_text.visible = True
            page.update()
            return

        send_btn.disabled = True
        send_btn.content = ft.Text(i18n.t("login.logging_in"))
        status_text.visible = False
        page.update()

        success, msg_key = await auth_service.request_password_reset(email)

        if success:
            status_text.value = i18n.t(msg_key)
            status_text.color = ft.Colors.GREEN
            status_text.visible = True
            send_btn.visible = False
            page.update()
            await asyncio.sleep(3)
            dlg.open = False
            page.update()
        else:
            status_text.value = i18n.t(msg_key)
            status_text.color = ft.Colors.RED
            status_text.visible = True
            send_btn.disabled = False
            send_btn.content = ft.Text(i18n.t("password_reset.send"))
            page.update()

    send_btn.on_click = send_clicked

    def close_dlg(e=None):
        dlg.open = False
        page.update()

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text(
            i18n.t("password_reset.title"),
            size=20,
            weight=ft.FontWeight.BOLD,
        ),
        content=ft.Column(
            controls=[
                ft.Text(i18n.t("password_reset.instruction"), size=14),
                email_field,
                status_text,
                send_btn,
            ],
            spacing=15,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        actions=[
            ft.TextButton(
                i18n.t("password_reset.cancel"),
                on_click=close_dlg,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    page.overlay.append(dlg)
    dlg.open = True
    page.update()


def create_main_menu_view(page: ft.Page) -> ft.Container:
    page._rebuild_view = lambda: create_main_menu_view(page)
    page.drawer = make_settings_drawer(page)

    user = auth_service.get_current_user()
    user_name = (
        (user.get("firstName", "") + " " + user.get("lastName", "")).strip()
        if user
        else "User"
    )
    user_email = user.get("email", "") if user else ""

    def go_to_warehouse(e):
        from desktop_alkozon.features.warehouse.views import create_warehouse_view

        page.clean()
        page.add(create_warehouse_view(page))
        page.update()

    def go_to_deliveries(e):
        from desktop_alkozon.features.deliveries.views import create_deliveries_view

        page.clean()
        page.add(create_deliveries_view(page))
        page.update()

    def go_to_employees(e):
        from desktop_alkozon.features.employees.views import create_employees_view

        page.clean()
        page.add(create_employees_view(page))
        page.update()

    def logout(e):
        auth_service.logout()
        page.clean()
        page.add(create_login_page_view(page))
        page.update()

    return ft.Stack(
        controls=[
            ft.Container(
                expand=True,
                padding=40,
                content=ft.Column(
                    expand=True,
                    controls=[
                        ft.Text(
                            "AlkozOn Desktop",
                            size=32,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            i18n.t("menu.logged_in_as", name=user_name),
                            size=16,
                        ),
                        ft.Text(
                            user_email,
                            size=12,
                            color=ft.Colors.GREY_400,
                        ),
                        ft.Divider(),
                        ft.ElevatedButton(
                            i18n.t("menu.warehouse"),
                            width=500,
                            height=60,
                            on_click=go_to_warehouse,
                        ),
                        ft.ElevatedButton(
                            i18n.t("menu.deliveries"),
                            width=500,
                            height=60,
                            on_click=go_to_deliveries,
                        ),
                        ft.ElevatedButton(
                            i18n.t("menu.employees"),
                            width=500,
                            height=60,
                            on_click=go_to_employees,
                        ),
                        ft.Divider(),
                        ft.ElevatedButton(
                            i18n.t("menu.logout"),
                            width=500,
                            height=50,
                            icon=ft.Icons.LOGOUT,
                            on_click=logout,
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.RED_700,
                                color=ft.Colors.WHITE,
                            ),
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                    scroll=ft.ScrollMode.AUTO,
                ),
            ),
            ft.Container(
                content=make_hamburger_button(page),
                left=12,
                top=12,
            ),
        ],
        expand=True,
    )
