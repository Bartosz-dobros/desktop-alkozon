import flet as ft

from desktop_alkozon.core.auth import auth_service
from desktop_alkozon.features.deliveries.controller import DeliveriesController


def create_deliveries_view(page: ft.Page) -> ft.Container:
    controller = DeliveriesController()
    couriers = []
    deliveries = []
    announcements = []

    couriers_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Email")),
            ft.DataColumn(ft.Text("Rola")),
            ft.DataColumn(ft.Text("Status")),
        ],
        rows=[],
    )

    deliveries_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Status")),
            ft.DataColumn(ft.Text("Adres")),
        ],
        rows=[],
    )

    announcements_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Tytul")),
            ft.DataColumn(ft.Text("Tresc")),
            ft.DataColumn(ft.Text("Utworzono")),
        ],
        rows=[],
    )

    loading = ft.ProgressRing(visible=False)

    courier_dropdown = ft.Dropdown(
        label="Wybierz kuriera",
        width=250,
        options=[],
    )
    destination_field = ft.TextField(
        label="Cel dostawy",
        width=250,
        max_length=150,
        text_size=14,
    )
    announcement_field = ft.TextField(
        label="Tresc ogloszenia",
        width=400,
        multiline=True,
        min_lines=2,
        max_length=500,
        text_size=14,
    )

    def refresh_tables():
        nonlocal couriers, deliveries, announcements
        couriers_table.rows.clear()
        if couriers:
            for c in couriers:
                status = "Aktywny" if c.get("active", False) else "Nieaktywny"
                role = c.get("role", "EMPLOYEE")
                couriers_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(c.get("id", 0)))),
                            ft.DataCell(ft.Text(c.get("email", ""))),
                            ft.DataCell(ft.Text(role)),
                            ft.DataCell(ft.Text(status)),
                        ]
                    )
                )

        deliveries_table.rows.clear()
        if deliveries:
            for d in deliveries:
                destination = (
                    d.addressSnapshot
                    if hasattr(d, "addressSnapshot") and d.addressSnapshot
                    else "Brak"
                )
                status = d.status.value if hasattr(d.status, "value") else str(d.status)
                deliveries_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(d.id))),
                            ft.DataCell(ft.Text(status)),
                            ft.DataCell(ft.Text(destination)),
                        ]
                    )
                )

        announcements_table.rows.clear()
        if announcements:
            for a in announcements:
                title = a.title if hasattr(a, "title") else ""
                content = a.content if hasattr(a, "content") else ""
                created = str(a.createdAt) if hasattr(a, "createdAt") else ""
                if created and "T" in created:
                    created = created.split("T")[0]
                announcements_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(a.id))),
                            ft.DataCell(ft.Text(title)),
                            ft.DataCell(
                                ft.Text(
                                    content[:50] + "..."
                                    if len(content) > 50
                                    else content
                                )
                            ),
                            ft.DataCell(ft.Text(created)),
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
        nonlocal couriers, deliveries, announcements
        try:
            loading.visible = True
            page.update()

            couriers = await controller.get_couriers() or []
            deliveries = await controller.get_deliveries() or []
            announcements = await controller.get_announcements() or []
            refresh_tables()

            courier_dropdown.options = [
                ft.dropdown.Option(c.get("email", ""))
                for c in couriers
                if c.get("email")
            ]

            loading.visible = False
            page.update()
        except Exception as e:
            print(f"Error loading deliveries data: {e}")
            couriers = controller.get_couriers_sync() or []
            deliveries = controller.get_deliveries_sync() or []
            announcements = []
            refresh_tables()
            courier_dropdown.options = []
            loading.visible = False
            show_error("Failed to load deliveries data. Please try again.")

    async def create_announcement_async(title, content_text):
        await controller.create_new_announcement(title, content_text)
        await load_data()

    def create_announcement_clicked(e):
        auth_service.update_activity()
        if not announcement_field.value.strip():
            snack = ft.SnackBar(
                content=ft.Text("Wpisz tresc ogloszenia"), duration=2000
            )
            page.overlay.append(snack)
            snack.open = True
            page.update()
            return

        title = (
            f"Dostawa - {destination_field.value.strip()}"
            if destination_field.value.strip()
            else "Ogloszenie dostawy"
        )

        page.run_task(
            create_announcement_async, title, announcement_field.value.strip()
        )

        destination_field.value = ""
        announcement_field.value = ""
        snack = ft.SnackBar(
            content=ft.Text("Ogloszenie dostawy utworzone"), duration=2000
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def go_to_menu(e):
        from desktop_alkozon.ui.pages.login_page import create_main_menu_view

        page.clean()
        page.add(create_main_menu_view(page))
        page.update()

    form = ft.Column(
        controls=[
            ft.Text("Nowe ogloszenie dostawy", size=16, weight=ft.FontWeight.BOLD),
            courier_dropdown,
            destination_field,
            announcement_field,
            ft.ElevatedButton(
                "Utworz ogloszenie dostawy", on_click=create_announcement_clicked
            ),
        ],
        spacing=10,
    )

    # Updated layout to expose tables and dropdown at top level for UI tests
    content = ft.Column(
        controls=[
            ft.Text("Kurierzy i stan dostaw", size=24, weight=ft.FontWeight.BOLD),
            ft.Text("Dostepni kurierzy", size=18),
            couriers_table,
            ft.Divider(),
            ft.Text("Aktualne dostawy", size=18),
            deliveries_table,
            ft.Divider(),
            ft.Text("Ogloszenia dostaw", size=18),
            announcements_table,
            ft.Divider(),
            courier_dropdown,
            # expose fields directly for UI tests
            destination_field,
            announcement_field,
            form,
            ft.ElevatedButton(
                "Powrot do menu glownego",
                width=400,
                on_click=go_to_menu,
            ),
        ],
        spacing=15,
    )

    page.run_task(load_data)

    return ft.Container(
        padding=20,
        content=content,
    )
