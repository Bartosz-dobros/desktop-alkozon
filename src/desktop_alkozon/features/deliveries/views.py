import flet as ft
from desktop_alkozon.features.deliveries.controller import DeliveriesController
from desktop_alkozon.core.auth import auth_service


def create_deliveries_view(page: ft.Page) -> ft.Container:
    controller = DeliveriesController()
    couriers = []
    deliveries = []

    couriers_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Kurier")),
            ft.DataColumn(ft.Text("Email")),
            ft.DataColumn(ft.Text("Status")),
        ],
        rows=[],
    )

    deliveries_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Kurier")),
            ft.DataColumn(ft.Text("Cel")),
            ft.DataColumn(ft.Text("Status")),
            ft.DataColumn(ft.Text("Ogłoszenie")),
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
        label="Treść ogłoszenia",
        width=400,
        multiline=True,
        min_lines=2,
        max_length=500,
        text_size=14,
    )

    def refresh_tables():
        nonlocal couriers, deliveries
        couriers_table.rows.clear()
        for c in couriers:
            couriers_table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(c.id))),
                    ft.DataCell(ft.Text(c.name)),
                    ft.DataCell(ft.Text(c.email)),
                    ft.DataCell(ft.Text(c.status)),
                ])
            )

        deliveries_table.rows.clear()
        for d in deliveries:
            deliveries_table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(d.id))),
                    ft.DataCell(ft.Text(d.courier_name)),
                    ft.DataCell(ft.Text(d.destination)),
                    ft.DataCell(ft.Text(d.status)),
                    ft.DataCell(ft.Text(d.announcement)),
                ])
            )

    async def load_data():
        nonlocal couriers, deliveries
        try:
            loading.visible = True
            page.update()

            couriers = await controller.get_couriers()
            deliveries = await controller.get_deliveries()
            refresh_tables()

            courier_dropdown.options = [ft.dropdown.Option(c.name) for c in couriers]

            loading.visible = False
            page.update()
        except Exception as e:
            print(f"Error loading deliveries data: {e}")
            couriers = controller.get_couriers_sync()
            deliveries = controller.get_deliveries_sync()
            refresh_tables()
            courier_dropdown.options = [ft.dropdown.Option(c.name) for c in couriers]
            loading.visible = False
            page.update()

    async def create_announcement_async(title, content_text):
        await controller.create_new_announcement(title, content_text)
        await load_data()

    def create_announcement_clicked(e):
        auth_service.update_activity()
        if not (courier_dropdown.value and destination_field.value.strip() and announcement_field.value.strip()):
            snack = ft.SnackBar(content=ft.Text("Wypełnij wszystkie pola"), duration=2000)
            page.overlay.append(snack)
            snack.open = True
            page.update()
            return

        title = f"Dostawa dla {courier_dropdown.value} - {destination_field.value}"
        
        page.run_task(create_announcement_async, title, announcement_field.value.strip())

        destination_field.value = ""
        announcement_field.value = ""
        snack = ft.SnackBar(content=ft.Text("Ogłoszenie dostawy utworzone"), duration=2000)
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
            ft.Text("Nowe ogłoszenie dostawy", size=16, weight=ft.FontWeight.BOLD),
            courier_dropdown,
            destination_field,
            announcement_field,
            ft.ElevatedButton("Utwórz ogłoszenie dostawy", on_click=create_announcement_clicked),
        ],
        spacing=10,
    )

    content = ft.Column(
        controls=[
            ft.Text("Kurierzy i stan dostaw", size=24, weight=ft.FontWeight.BOLD),
            ft.Text("Dostępni kurierzy", size=18),
            ft.Row([loading, couriers_table]),
            ft.Divider(),
            ft.Text("Aktualne dostawy", size=18),
            deliveries_table,
            ft.Divider(),
            form,
            ft.ElevatedButton(
                "Powrót do menu głównego",
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
