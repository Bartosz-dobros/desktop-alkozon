import flet as ft

from desktop_alkozon.core.auth import auth_service
from desktop_alkozon.core.i18n import i18n
from desktop_alkozon.features.warehouse.controller import WarehouseController


def create_warehouse_view(page: ft.Page) -> ft.Container:
    page._rebuild_view = lambda: create_warehouse_view(page)

    controller = WarehouseController()
    items = []

    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text(i18n.t("warehouse.table.id"))),
            ft.DataColumn(ft.Text(i18n.t("warehouse.table.name"))),
            ft.DataColumn(ft.Text(i18n.t("warehouse.table.quantity"))),
            ft.DataColumn(ft.Text(i18n.t("warehouse.table.zone"))),
        ],
        rows=[],
    )
    table_loading = ft.ProgressRing(visible=False)

    product_id_field = ft.TextField(
        label=i18n.t("warehouse.product_id"),
        width=120,
        input_filter=ft.InputFilter(allow=True, regex_string=r"^[0-9]*$"),
        keyboard_type=ft.KeyboardType.NUMBER,
        text_size=14,
    )
    quantity_field = ft.TextField(
        label=i18n.t("warehouse.quantity"),
        width=150,
        input_filter=ft.InputFilter(allow=True, regex_string=r"^-?[0-9]*$"),
        keyboard_type=ft.KeyboardType.NUMBER,
        text_size=14,
    )
    note_field = ft.TextField(
        label=i18n.t("warehouse.note"),
        width=300,
        max_length=200,
        text_size=14,
    )

    product_count_text = ft.Text("0 produktow", size=14)

    def refresh_table():
        table.rows.clear()
        if not items:
            product_count_text.value = i18n.t("warehouse.count", count=0)
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
        product_count_text.value = i18n.t("warehouse.count", count=len(items))

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
            show_error(i18n.t("warehouse.load_error"))

    async def order_item_async(product_id, quantity_delta, note):
        result = await controller.order_new_item(product_id, quantity_delta, note)
        if result:
            show_success(i18n.t("warehouse.order_success"))
        else:
            show_error(i18n.t("warehouse.order_fail"))
        await load_data()

    def order_item_clicked(e):
        auth_service.update_activity()
        if not product_id_field.value or not quantity_field.value:
            show_error(i18n.t("warehouse.enter_product_id"))
            return

        try:
            product_id = int(product_id_field.value)
            quantity_delta = int(quantity_field.value)
        except ValueError:
            show_error(i18n.t("warehouse.invalid_input"))
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

    form = ft.Row(
        controls=[
            product_id_field,
            quantity_field,
            note_field,
            ft.ElevatedButton(
                i18n.t("warehouse.order_button"), on_click=order_item_clicked
            ),
        ],
        spacing=10,
    )

    content = ft.Column(
        expand=True,
        controls=[
            ft.Text(
                i18n.t("warehouse.title"),
                size=24,
                weight=ft.FontWeight.BOLD,
            ),
            ft.Row([table_loading, product_count_text]),
            table,
            ft.Divider(),
            ft.Text(
                i18n.t("warehouse.new_order_title"),
                size=18,
                weight=ft.FontWeight.BOLD,
            ),
            product_id_field,
            quantity_field,
            note_field,
            form,
            ft.ElevatedButton(
                i18n.t("warehouse.back"),
                width=400,
                on_click=go_to_menu,
            ),
        ],
        spacing=15,
        scroll=ft.ScrollMode.AUTO,
    )

    page.run_task(load_data)

    container = ft.Container(
        expand=True,
        padding=20,
        content=content,
    )
    container.controls = content.controls
    return container
