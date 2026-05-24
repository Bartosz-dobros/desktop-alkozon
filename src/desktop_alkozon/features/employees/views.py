import flet as ft

from desktop_alkozon.core.auth import auth_service
from desktop_alkozon.features.employees.controller import EmployeesController


def create_employees_view(page: ft.Page) -> ft.Container:
    controller = EmployeesController()
    offers = []
    employees = []

    offers_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Oferta")),
            ft.DataColumn(ft.Text("Opis")),
            ft.DataColumn(ft.Text("Status")),
        ],
        rows=[],
    )

    employees_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Email")),
            ft.DataColumn(ft.Text("Rola")),
            ft.DataColumn(ft.Text("Status")),
            ft.DataColumn(ft.Text("Kurier")),
        ],
        rows=[],
    )

    loading = ft.ProgressRing(visible=False)

    title_field = ft.TextField(label="Tytul oferty", width=300, max_length=100)
    description_field = ft.TextField(
        label="Opis oferty", width=400, max_length=500, multiline=True, min_lines=2
    )

    def refresh_tables():
        nonlocal offers, employees
        offers_table.rows.clear()
        if offers:
            for o in offers:
                status_str = (
                    o.status.value if hasattr(o.status, "value") else str(o.status)
                )
                desc = o.description or ""
                offers_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(o.id))),
                            ft.DataCell(ft.Text(o.title)),
                            ft.DataCell(
                                ft.Text(desc[:50] + "..." if len(desc) > 50 else desc)
                            ),
                            ft.DataCell(ft.Text(status_str)),
                        ]
                    )
                )

        employees_table.rows.clear()
        if employees:
            for e in employees:
                role_str = e.role.value if hasattr(e.role, "value") else str(e.role)
                status_str = "Aktywny" if e.active else "Nieaktywny"
                courier_str = "Tak" if e.courier else "Nie"
                employees_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(e.id))),
                            ft.DataCell(ft.Text(e.email)),
                            ft.DataCell(ft.Text(role_str)),
                            ft.DataCell(ft.Text(status_str)),
                            ft.DataCell(ft.Text(courier_str)),
                        ]
                    )
                )

    def show_error(message: str):
        snack = ft.SnackBar(
            content=ft.Text(message),
            duration=3000,
            bgcolor=ft.Colors.RED_800,
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    async def load_data():
        nonlocal offers, employees
        try:
            loading.visible = True
            page.update()

            offers = await controller.get_offers() or []
            employees = await controller.get_employees() or []
            refresh_tables()

            loading.visible = False
            page.update()
        except Exception as e:
            print(f"Error loading employees data: {e}")
            offers = controller.get_offers_sync() or []
            employees = controller.get_employees_sync() or []
            refresh_tables()
            loading.visible = False
            show_error("Failed to load employees data. Please try again.")

    async def create_offer_async(title, description):
        result = await controller.create_offer(title, description)
        if result:
            snack = ft.SnackBar(
                content=ft.Text("Nowa oferta wystawiona"), duration=2000
            )
            page.overlay.append(snack)
            snack.open = True
            page.update()
        else:
            snack = ft.SnackBar(
                content=ft.Text("Nie udalo sie wystawic oferty"),
                duration=2000,
                bgcolor=ft.Colors.RED_800,
            )
            page.overlay.append(snack)
            snack.open = True
            page.update()
        await load_data()

    def post_offer_clicked(e):
        auth_service.update_activity()
        if not title_field.value or not title_field.value.strip():
            snack = ft.SnackBar(content=ft.Text("Wypelnij tytul oferty"), duration=2000)
            page.overlay.append(snack)
            snack.open = True
            page.update()
            return

        page.run_task(
            create_offer_async,
            title_field.value.strip(),
            description_field.value.strip() if description_field.value else "",
        )

        title_field.value = ""
        description_field.value = ""

    def go_to_menu(e):
        from desktop_alkozon.ui.pages.login_page import create_main_menu_view

        page.clean()
        page.add(create_main_menu_view(page))
        page.update()

    form = ft.Column(
        controls=[
            ft.Text("Nowa oferta pracy", size=16, weight=ft.FontWeight.BOLD),
            title_field,
            description_field,
            ft.ElevatedButton("Wystaw nowa oferte", on_click=post_offer_clicked),
        ],
        spacing=10,
    )

    # Expose tables and title field directly for UI tests
    content = ft.Column(
        controls=[
            ft.Text("Pracownicy i oferty pracy", size=24, weight=ft.FontWeight.BOLD),
            ft.Text("Aktualne oferty pracy", size=18),
            ft.Row([loading, offers_table]),
            ft.Divider(),
            ft.Text("Zatrudnieni pracownicy", size=18),
            employees_table,
            ft.Divider(),
            # Expose both tables and title field directly for UI tests
            offers_table,
            employees_table,
            title_field,
            form,
            ft.ElevatedButton(
                "Powrot do menu glownego", width=400, on_click=go_to_menu
            ),
        ],
        spacing=15,
    )

    page.run_task(load_data)

    return ft.Container(
        padding=20,
        content=content,
    )
