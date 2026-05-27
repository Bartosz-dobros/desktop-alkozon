import flet as ft

from desktop_alkozon.core.auth import auth_service
from desktop_alkozon.core.i18n import i18n
from desktop_alkozon.features.warehouse.controller import WarehouseController

RECEIVED_ORDER_IDS: set[int] = set()


def _show_snack(page: ft.Page, message: str, is_error: bool = False):
    snack = ft.SnackBar(
        content=ft.Text(message),
        duration=3000,
        bgcolor=ft.Colors.RED_800 if is_error else ft.Colors.GREEN_800,
    )
    page.overlay.append(snack)
    snack.open = True
    page.update()


def _go_to_menu(page: ft.Page):
    from desktop_alkozon.ui.pages.login_page import create_main_menu_view

    page.clean()
    page.add(create_main_menu_view(page))
    page.update()


def _back_to_hub(page: ft.Page):
    page.clean()
    page.add(create_warehouse_view(page))
    page.update()


def _is_manager() -> bool:
    user = auth_service.get_current_user()
    return user is not None and user.get("role") == "MANAGER"


def create_warehouse_view(page: ft.Page) -> ft.Container:
    page._rebuild_view = lambda: create_warehouse_view(page)

    def go_to_state(e):
        page.clean()
        page.add(create_warehouse_state_view(page))
        page.update()

    def go_to_orders(e):
        page.clean()
        page.add(create_warehouse_orders_view(page))
        page.update()

    def go_to_menu(e):
        _go_to_menu(page)

    is_manager = _is_manager()
    orders_btn = ft.ElevatedButton(
        i18n.t("warehouse.orders_button"),
        width=400,
        height=60,
        on_click=go_to_orders if is_manager else None,
        disabled=not is_manager,
        tooltip=None if is_manager else i18n.t("warehouse.manager_only"),
    )

    return ft.Container(
        expand=True,
        padding=20,
        content=ft.Column(
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15,
            controls=[
                ft.Text(
                    i18n.t("warehouse.menu_title"), size=24, weight=ft.FontWeight.BOLD
                ),
                ft.Divider(),
                ft.ElevatedButton(
                    i18n.t("warehouse.state_button"),
                    width=400,
                    height=60,
                    on_click=go_to_state,
                ),
                orders_btn,
                ft.Divider(),
                ft.ElevatedButton(
                    i18n.t("warehouse.back"),
                    width=400,
                    on_click=go_to_menu,
                ),
            ],
        ),
    )


def create_warehouse_state_view(page: ft.Page) -> ft.Container:
    page._rebuild_view = lambda: create_warehouse_state_view(page)

    controller = WarehouseController()

    loading = ft.ProgressRing(visible=True)

    product_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text(i18n.t("warehouse.table.id"))),
            ft.DataColumn(ft.Text(i18n.t("warehouse.table.name"))),
            ft.DataColumn(ft.Text(i18n.t("warehouse.table.quantity"))),
            ft.DataColumn(ft.Text(i18n.t("warehouse.table.zone"))),
        ],
        rows=[],
    )
    product_count = ft.Text("", size=13)

    raw_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text(i18n.t("warehouse.raw_table.id"))),
            ft.DataColumn(ft.Text(i18n.t("warehouse.raw_table.name"))),
            ft.DataColumn(ft.Text(i18n.t("warehouse.raw_table.unit"))),
            ft.DataColumn(ft.Text(i18n.t("warehouse.raw_table.quantity"))),
        ],
        rows=[],
    )
    raw_count = ft.Text("", size=13)

    async def load_data():
        try:
            loading.visible = True
            page.update()

            products = await controller.get_products()
            product_table.rows.clear()
            for p in products:
                product_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(p.productId))),
                            ft.DataCell(ft.Text(p.name)),
                            ft.DataCell(ft.Text(str(p.quantity))),
                            ft.DataCell(ft.Text(p.warehouseZone or "-")),
                        ]
                    )
                )
            product_count.value = i18n.t("warehouse.count", count=len(products))

            materials = await controller.get_raw_materials()
            raw_table.rows.clear()
            for m in materials:
                raw_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(m.id))),
                            ft.DataCell(ft.Text(m.name)),
                            ft.DataCell(ft.Text(m.unit)),
                            ft.DataCell(ft.Text(str(m.quantity))),
                        ]
                    )
                )
            raw_count.value = i18n.t("warehouse.raw_count", count=len(materials))

            loading.visible = False
            page.update()
        except Exception:
            products = controller.get_products_sync()
            product_table.rows.clear()
            for p in products:
                product_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(p.productId))),
                            ft.DataCell(ft.Text(p.name)),
                            ft.DataCell(ft.Text(str(p.quantity))),
                            ft.DataCell(ft.Text(p.warehouseZone or "-")),
                        ]
                    )
                )
            product_count.value = i18n.t("warehouse.count", count=len(products))

            materials = controller.get_raw_materials_sync()
            raw_table.rows.clear()
            for m in materials:
                raw_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(m.id))),
                            ft.DataCell(ft.Text(m.name)),
                            ft.DataCell(ft.Text(m.unit)),
                            ft.DataCell(ft.Text(str(m.quantity))),
                        ]
                    )
                )
            raw_count.value = i18n.t("warehouse.raw_count", count=len(materials))

            loading.visible = False
            _show_snack(page, i18n.t("warehouse.load_error"), is_error=True)
            page.update()

    page.run_task(load_data)

    return ft.Container(
        expand=True,
        padding=20,
        content=ft.Column(
            expand=True,
            spacing=15,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Text(
                    i18n.t("warehouse.state_title"),
                    size=24,
                    weight=ft.FontWeight.BOLD,
                ),
                loading,
                ft.Text(
                    i18n.t("warehouse.products_section"),
                    size=18,
                    weight=ft.FontWeight.BOLD,
                ),
                product_count,
                product_table,
                ft.Divider(),
                ft.Text(
                    i18n.t("warehouse.raw_materials_section"),
                    size=18,
                    weight=ft.FontWeight.BOLD,
                ),
                raw_count,
                raw_table,
                ft.ElevatedButton(
                    i18n.t("warehouse.back_to_hub"),
                    width=400,
                    on_click=lambda e: _back_to_hub(page),
                ),
            ],
        ),
    )


def create_warehouse_orders_view(page: ft.Page) -> ft.Container:
    page._rebuild_view = lambda: create_warehouse_orders_view(page)

    controller = WarehouseController()
    orders: list = []
    loading = ft.ProgressRing(visible=True)

    order_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text(i18n.t("warehouse.orders.table.id"))),
            ft.DataColumn(ft.Text(i18n.t("warehouse.orders.table.status"))),
            ft.DataColumn(ft.Text(i18n.t("warehouse.orders.table.note"))),
            ft.DataColumn(ft.Text(i18n.t("warehouse.orders.table.date"))),
            ft.DataColumn(ft.Text(i18n.t("warehouse.orders.table.lines"))),
            ft.DataColumn(ft.Text(i18n.t("warehouse.orders.table.actions"))),
        ],
        rows=[],
    )

    new_order_btn = ft.ElevatedButton(
        i18n.t("warehouse.orders.new_order_button"),
        icon=ft.Icons.ADD,
        on_click=lambda e: _open_new_order_dialog(page, controller, load_data),
    )

    def format_lines(lines) -> str:
        if not lines:
            return "-"
        parts = []
        for ln in lines:
            name = (
                ln.productName
                or ln.rawMaterialName
                or f"#{ln.productId or ln.rawMaterialId}"
            )
            parts.append(f"{name} x{ln.quantityDelta}")
        return "; ".join(parts)

    async def load_data():
        nonlocal orders
        try:
            loading.visible = True
            page.update()

            orders = await controller.get_replenishment_history()

            order_table.rows.clear()
            for o in orders:
                is_received = o.id in RECEIVED_ORDER_IDS or o.status != "PENDING"
                lines_text = format_lines(o.lines)
                created = o.createdAt.strftime("%Y-%m-%d %H:%M") if o.createdAt else "-"

                action_btn = None
                if is_received:
                    action_btn = ft.Container(
                        content=ft.Text(
                            i18n.t("warehouse.orders.received_badge"),
                            color=ft.Colors.GREEN,
                            weight=ft.FontWeight.BOLD,
                            size=13,
                        ),
                    )
                else:
                    action_btn = ft.ElevatedButton(
                        i18n.t("warehouse.orders.mark_received"),
                        on_click=lambda _, oid=o.id: _mark_received(
                            page, controller, oid, load_data
                        ),
                        height=36,
                        style=ft.ButtonStyle(padding=ft.Padding(8, 4, 8, 4)),
                    )

                order_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(o.id))),
                            ft.DataCell(ft.Text(o.status or "PENDING")),
                            ft.DataCell(ft.Text(o.note or "-")),
                            ft.DataCell(ft.Text(created)),
                            ft.DataCell(
                                ft.Container(
                                    content=ft.Text(lines_text, size=12),
                                    width=200,
                                )
                            ),
                            ft.DataCell(
                                ft.Container(
                                    content=action_btn,
                                )
                            ),
                        ]
                    )
                )

            loading.visible = False
            page.update()
        except Exception as ex:
            msg = i18n.t("warehouse.api_conn_error")
            status = getattr(ex, "response", None)
            if status is not None:
                code = getattr(status, "status_code", "?")
                msg = f"{i18n.t('warehouse.load_error')} (HTTP {code})"
            _show_snack(page, msg, is_error=True)
            loading.visible = False
            page.update()

    page.run_task(load_data)

    return ft.Container(
        expand=True,
        padding=20,
        content=ft.Column(
            expand=True,
            spacing=15,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Text(
                    i18n.t("warehouse.orders_title"),
                    size=24,
                    weight=ft.FontWeight.BOLD,
                ),
                new_order_btn,
                loading,
                order_table,
                ft.ElevatedButton(
                    i18n.t("warehouse.back_to_hub"),
                    width=400,
                    on_click=lambda e: _back_to_hub(page),
                ),
            ],
        ),
    )


def _open_new_order_dialog(
    page: ft.Page,
    controller: WarehouseController,
    reload_callback,
):
    line_rows: list[dict] = []
    lines_container = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO)

    note_field = ft.TextField(
        label=i18n.t("warehouse.orders.note_label"),
        width=350,
        max_length=200,
        text_size=14,
    )

    status_text = ft.Text("", size=14, visible=False)

    def rebuild_lines():
        lines_container.controls.clear()
        for idx, row_data in enumerate(line_rows):
            pid_field = row_data["pid"]
            qty_field = row_data["qty"]

            line_row = ft.Row(
                controls=[
                    ft.Text(str(idx + 1) + ".", width=25),
                    pid_field,
                    qty_field,
                    ft.IconButton(
                        icon=ft.Icons.DELETE,
                        icon_size=18,
                        on_click=lambda _, i=idx: _remove_line(i),
                        tooltip=i18n.t("warehouse.orders.remove_line"),
                    ),
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
            lines_container.controls.append(line_row)
        page.update()

    def _remove_line(idx: int):
        if 0 <= idx < len(line_rows):
            line_rows.pop(idx)
            rebuild_lines()

    def add_line(e):
        pid = ft.TextField(
            label=i18n.t("warehouse.orders.product_id"),
            width=120,
            input_filter=ft.InputFilter(allow=True, regex_string=r"^[0-9]*$"),
            keyboard_type=ft.KeyboardType.NUMBER,
            text_size=14,
        )
        qty = ft.TextField(
            label=i18n.t("warehouse.orders.quantity_delta"),
            width=130,
            input_filter=ft.InputFilter(allow=True, regex_string=r"^-?[0-9]*$"),
            keyboard_type=ft.KeyboardType.NUMBER,
            text_size=14,
        )
        line_rows.append({"pid": pid, "qty": qty})
        rebuild_lines()

    async def submit_order(e):
        if not line_rows:
            status_text.value = i18n.t("warehouse.enter_product_id")
            status_text.color = ft.Colors.RED
            status_text.visible = True
            page.update()
            return

        note = note_field.value.strip() if note_field.value else None
        success_count = 0
        fail_count = 0

        for row_data in line_rows:
            pid_val = row_data["pid"].value
            qty_val = row_data["qty"].value
            if not pid_val or not qty_val:
                fail_count += 1
                continue
            try:
                pid = int(pid_val)
                qty = int(qty_val)
                result = await controller.order_new_item(pid, qty, note)
                if result:
                    success_count += 1
                else:
                    fail_count += 1
            except ValueError:
                fail_count += 1

        dlg.open = False
        page.update()

        if success_count > 0:
            _show_snack(
                page,
                i18n.t("warehouse.orders.create_success"),
            )
        if fail_count > 0:
            _show_snack(
                page,
                i18n.t("warehouse.orders.create_fail"),
                is_error=True,
            )

        await reload_callback()

    add_line(None)

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text(
            i18n.t("warehouse.orders.create_title"),
            size=20,
            weight=ft.FontWeight.BOLD,
        ),
        content=ft.Column(
            width=450,
            height=400,
            controls=[
                lines_container,
                ft.ElevatedButton(
                    i18n.t("warehouse.orders.add_line"),
                    icon=ft.Icons.ADD,
                    on_click=add_line,
                ),
                ft.Divider(height=10),
                note_field,
                status_text,
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        ),
        actions=[
            ft.TextButton(
                i18n.t("warehouse.orders.cancel"),
                on_click=lambda e: setattr(dlg, "open", False) or page.update(),
            ),
            ft.ElevatedButton(
                i18n.t("warehouse.orders.create_button"),
                on_click=lambda e: page.run_task(submit_order, e),
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    page.overlay.append(dlg)
    dlg.open = True
    page.update()


async def _mark_received(
    page: ft.Page,
    controller: WarehouseController,
    order_id: int,
    reload_callback,
):
    auth_service.update_activity()
    success = await controller.mark_received(order_id)
    if success:
        RECEIVED_ORDER_IDS.add(order_id)
        _show_snack(page, i18n.t("warehouse.orders.received_success"))
    else:
        _show_snack(page, i18n.t("warehouse.orders.received_fail"), is_error=True)
    await reload_callback()
