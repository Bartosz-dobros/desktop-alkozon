import flet as ft
from desktop_alkozon.core.auth import auth_service


def create_login_page_view(page: ft.Page) -> ft.Container:
    loading = [False]
    
    username_field = ft.TextField(
        label="Username / Email",
        width=400,
        border_radius=8,
        prefix_icon=ft.Icons.PERSON,
        max_length=50,
        text_size=16,
    )
    password_field = ft.TextField(
        label="Password",
        password=True,
        can_reveal_password=True,
        width=400,
        border_radius=8,
        prefix_icon=ft.Icons.LOCK,
        max_length=128,
        text_size=16,
    )
    two_fa_field = ft.TextField(
        label="2FA Code (6 digits)",
        width=400,
        border_radius=8,
        visible=False,
        max_length=6,
        input_filter=ft.InputFilter(allow=True, regex_string=r"^[0-9]*$"),
        keyboard_type=ft.KeyboardType.NUMBER,
        text_size=16,
    )
    login_button = ft.ElevatedButton(
        content=ft.Text("LOGIN"),
        width=400,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
    )
    status_text = ft.Text("", color=ft.Colors.RED, size=14, visible=False)

    async def login_clicked(e):
        if loading[0]:
            return

        loading[0] = True
        login_button.disabled = True
        login_button.content = ft.Text("LOGGING IN...")
        status_text.visible = False
        page.update()

        success = await auth_service.login(
            username_field.value or "",
            password_field.value or "",
            two_fa_field.value if two_fa_field.visible else None
        )

        if success:
            loading[0] = False
            page.clean()
            page.add(create_main_menu_view(page))
        else:
            loading[0] = False
            login_button.disabled = False
            login_button.content = ft.Text("LOGIN")
            if auth_service.is_locked():
                status_text.value = "Account locked. Restart the app."
                status_text.visible = True
                login_button.disabled = True
            else:
                remaining = max(0, 5 - auth_service.attempts)
                status_text.value = f"Login failed. Attempts left: {remaining}"
                status_text.visible = True
                if auth_service.attempts >= 3:
                    two_fa_field.visible = True

        page.update()

    login_button.on_click = login_clicked

    return ft.Container(
        padding=40,
        alignment=ft.Alignment(0.5, 0.5),
        content=ft.Column(
            controls=[
                ft.Text("AlkozOn Desktop", size=32, weight=ft.FontWeight.BOLD),
                ft.Text("Log in to access warehouse, deliveries & employees", size=16),
                ft.Divider(),
                username_field,
                password_field,
                two_fa_field,
                status_text,
                login_button,
                ft.TextButton("Forgot password?", on_click=lambda e: print("TODO: reset")),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        ),
    )


def create_main_menu_view(page: ft.Page) -> ft.Container:
    user = auth_service.get_current_user()
    user_name = (user.get("firstName", "") + " " + user.get("lastName", "")).strip() if user else "User"
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

    return ft.Container(
        padding=40,
        alignment=ft.Alignment(0.5, 0.5),
        content=ft.Column(
            controls=[
                ft.Text("AlkozOn Desktop", size=32, weight=ft.FontWeight.BOLD),
                ft.Text(f"Zalogowany jako: {user_name}", size=16),
                ft.Text(user_email, size=12, color=ft.Colors.GREY_400),
                ft.Divider(),
                ft.ElevatedButton("Stan magazynu i zamówienia", width=500, height=60, on_click=go_to_warehouse),
                ft.ElevatedButton("Kurierzy i dostawy", width=500, height=60, on_click=go_to_deliveries),
                ft.ElevatedButton("Pracownicy i oferty pracy", width=500, height=60, on_click=go_to_employees),
                ft.Divider(),
                ft.ElevatedButton(
                    "Wyloguj się",
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
        ),
    )
