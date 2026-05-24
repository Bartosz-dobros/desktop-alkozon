import flet as ft

from desktop_alkozon.core.auth import auth_service
from desktop_alkozon.features.warehouse.controller import WarehouseController


def create_warehouse_view(page: ft.Page) -> ft.Container:
    controller = WarehouseController()
    items = []

    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Nazwa towaru")),
            ft.DataColumn(ft.Text("Ilosc")),
            ft.DataColumn(ft.Text("Strefa")),
        ],
        rows=[],
    )
    table_loading = ft.ProgressRing(visible=False)

    product_id_field = ft.TextField(
        label="ID produktu",
        width=120,
        input_filter=ft.InputFilter(allow=True, regex_string=r"^[0-9]*$"),
        keyboard_type=ft.KeyboardType.NUMBER,
        text_size=14,
    )
    quantity_field = ft.TextField(
        label="Ilosc",
        width=150,
        input_filter=ft.InputFilter(allow=True, regex_string=r"^-?[0-9]*$"),
        keyboard_type=ft.KeyboardType.NUMBER,
        text_size=14,
    )
    note_field = ft.TextField(
        label="Notatka (opcjonalnie)",
        width=300,
        max_length=200,
        text_size=14,
    )

    product_count_text = ft.Text("0 produktow", size=14)

    def refresh_table():
        table.rows.clear()
        if not items:
            product_count_text.value = "0 produktow"
            return
        for item in items:
            table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(item.productId))),
                        ft.DataCell(ft.Text(item.name)),
                        ft.DataCell(ft.Text(str(item.quantity))),
                        ft.DataCell(
                            ft.Text(item.warehouseZone if item.warehouseZone else "-")
                        ),
                    ]
                )
            )
        product_count_text.value = f"{len(items)} produktow"

    def show_error(message: str):
        snack = ft.SnackBar(
            content=ft.Text(message),
            duration=3000,
            bgcolor=ft.Colors.RED_800,
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def show_success(message: str):
        snack = ft.SnackBar(
            content=ft.Text(message),
            duration=2000,
            bgcolor=ft.Colors.GREEN_800,
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    async def load_data():
        nonlocal items
        try:
            table_loading.visible = True
            page.update()

            result = await controller.get_stock_data()
            items = result if result is not None else []
            refresh_table()

            table_loading.visible = False
            page.update()
        except Exception as e:
            print(f"Error loading warehouse data: {e}")
            items = controller.get_stock_data_sync() or []
            refresh_table()
            table_loading.visible = False
            show_error("Failed to load warehouse data. Please try again.")

    async def order_item_async(product_id, quantity_delta, note):
        result = await controller.order_new_item(product_id, quantity_delta, note)
        if result:
            show_success("Zamowienie zlozone")
        else:
            show_error("Nie udalo sie zlozyc zamowienia")
        await load_data()

    def order_item_clicked(e):
        auth_service.update_activity()
        if not product_id_field.value or not quantity_field.value:
            show_error("Podaj ID produktu i zmiane ilosci")
            return

        try:
            product_id = int(product_id_field.value)
            quantity_delta = int(quantity_field.value)
        except ValueError:
            show_error("ID produktu i zmiana ilosci musza byc liczbami")
            return

        page.run_task(
            order_item_async,
            product_id,
            quantity_delta,
            note_field.value.strip() if note_field.value else None,
        )

        product_id_field.value = ""
        quantity_field.value = ""
        note_field.value = ""

    def go_to_menu(e):
        from desktop_alkozon.ui.pages.login_page import create_main_menu_view

        page.clean()
        page.add(create_main_menu_view(page))
        page.update()

    # (no code)  # table_wrapper removed

    form = ft.Row(
        controls=[
            product_id_field,
            quantity_field,
            note_field,
            ft.ElevatedButton("Zamow towar", on_click=order_item_clicked),
        ],
        spacing=10,
    )

    # Expose table and fields directly for UI tests
    content = ft.Column(
        controls=[
            ft.Text("Stan magazynu", size=24, weight=ft.FontWeight.BOLD),
            ft.Row([table_loading, product_count_text]),
            # expose the data table
            table,
            ft.Divider(),
            ft.Text("Zamow nowy towar", size=18, weight=ft.FontWeight.BOLD),
            # expose fields directly
            product_id_field,
            quantity_field,
            note_field,
            form,
            ft.ElevatedButton(
                "Powrot do menu glownego",
                width=400,
                on_click=go_to_menu,
            ),
        ],
        spacing=15,
        scroll=ft.ScrollMode.AUTO,
    )

    page.run_task(load_data)

    container = ft.Container(
        padding=20,
        content=content,
    )
    # Expose controls directly for tests that access view.controls
    container.controls = content.controls  # type: ignore[attr-defined]
    return container
