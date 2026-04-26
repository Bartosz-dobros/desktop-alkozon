import flet as ft
from desktop_alkozon.features.warehouse.controller import WarehouseController
from desktop_alkozon.core.auth import auth_service


def create_warehouse_view(page: ft.Page) -> ft.Container:
    controller = WarehouseController()
    items = []

    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Nazwa towaru")),
            ft.DataColumn(ft.Text("Ilość")),
            ft.DataColumn(ft.Text("Jednostka")),
            ft.DataColumn(ft.Text("Cena")),
        ],
        rows=[],
    )
    table_loading = ft.ProgressRing(visible=False)

    name_field = ft.TextField(
        label="Nazwa towaru",
        width=300,
        max_length=100,
        text_size=14,
    )
    quantity_field = ft.TextField(
        label="Ilość",
        width=120,
        max_length=5,
        input_filter=ft.InputFilter(allow=True, regex_string=r"^[0-9]*$"),
        keyboard_type=ft.KeyboardType.NUMBER,
        text_size=14,
    )
    unit_field = ft.TextField(
        label="Jednostka",
        width=100,
        value="szt.",
        max_length=10,
        text_size=14,
    )
    price_field = ft.TextField(
        label="Cena",
        width=120,
        max_length=10,
        input_filter=ft.InputFilter(allow=True, regex_string=r"^\d*\.?\d*$"),
        keyboard_type=ft.KeyboardType.NUMBER,
        text_size=14,
    )

    def refresh_table():
        table.rows.clear()
        for item in items:
            table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(item.id))),
                        ft.DataCell(ft.Text(item.name)),
                        ft.DataCell(ft.Text(str(item.quantity))),
                        ft.DataCell(ft.Text(item.unit)),
                        ft.DataCell(ft.Text(f"{item.price:.2f} zł")),
                    ]
                )
            )

    async def load_data():
        nonlocal items
        try:
            table_loading.visible = True
            page.update()
            
            items = await controller.get_stock_data()
            refresh_table()
            
            table_loading.visible = False
            page.update()
        except Exception as e:
            print(f"Error loading warehouse data: {e}")
            items = controller.get_stock_data_sync()
            refresh_table()
            table_loading.visible = False
            page.update()

    async def add_item_async(name, quantity, unit, price):
        await controller.order_new_item(name, quantity, unit, price)
        await load_data()

    def add_item_clicked(e):
        auth_service.update_activity()
        if not (name_field.value and name_field.value.strip() and
                quantity_field.value and quantity_field.value.strip() and
                unit_field.value and unit_field.value.strip() and
                price_field.value and price_field.value.strip()):
            snack = ft.SnackBar(content=ft.Text("Wszystkie pola muszą być wypełnione"), duration=2000)
            page.overlay.append(snack)
            snack.open = True
            page.update()
            return

        try:
            page.run_task(add_item_async, name_field.value.strip(), int(quantity_field.value), unit_field.value.strip(), float(price_field.value))
            name_field.value = ""
            quantity_field.value = ""
            unit_field.value = "szt."
            price_field.value = ""

            snack = ft.SnackBar(content=ft.Text("Zamówienie złożone"), duration=2000)
            page.overlay.append(snack)
            snack.open = True
            page.update()
        except ValueError:
            snack = ft.SnackBar(content=ft.Text("Wypełnij poprawnie wszystkie pola"), duration=2000)
            page.overlay.append(snack)
            snack.open = True
            page.update()

    def go_to_menu(e):
        from desktop_alkozon.ui.pages.login_page import create_main_menu_view
        page.clean()
        page.add(create_main_menu_view(page))
        page.update()

    form = ft.Row(
        controls=[
            name_field,
            quantity_field,
            unit_field,
            price_field,
            ft.ElevatedButton("Zamów nowy towar", on_click=add_item_clicked),
        ],
        spacing=10,
    )

    content = ft.Column(
        controls=[
            ft.Text("Stan magazynu", size=24, weight=ft.FontWeight.BOLD),
            ft.Row([table_loading, table]),
            ft.Divider(),
            ft.Text("Zamów nowy towar", size=18, weight=ft.FontWeight.BOLD),
            form,
            ft.ElevatedButton(
                "Powrót do menu głównego",
                width=400,
                on_click=go_to_menu,
            ),
        ],
        spacing=20,
    )

    page.run_task(load_data)

    return ft.Container(
        padding=20,
        content=content,
    )
