import flet as ft
from desktop_alkozon.core.auth import auth_service


def create_main_menu_view(page: ft.Page) -> ft.Container:
    user = auth_service.get_current_user()
    user_name = user.get("firstName", "") + " " + user.get("lastName", "") if user else "User"
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
        from desktop_alkozon.ui.pages.login_page import create_login_page_view
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
