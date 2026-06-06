import flet as ft

from desktop_alkozon.core.auth import auth_service
from desktop_alkozon.core.connectivity import connectivity_service
from desktop_alkozon.core.i18n import i18n
from desktop_alkozon.features.warehouse.controller import WarehouseController

RECEIVED_ORDER_IDS: set[int] = set()


def _show_snack(
    page: ft.Page, message: str, is_error: bool = False, is_warning: bool = False
):
    if is_warning:
        bgcolor = ft.Colors.AMBER_700
    elif is_error:
        bgcolor = ft.Colors.RED_800
    else:
        bgcolor = ft.Colors.GREEN_800
    snack = ft.SnackBar(
        content=ft.Text(message),
        duration=3000,
        bgcolor=bgcolor,
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
    _products: list = []
    _raw_materials: list = []
    _highest_id = 0
    loading = ft.ProgressRing(visible=True)

    pending_table = ft.DataTable(
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
    received_table = ft.DataTable(
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
    pending_count = ft.Text("", size=13)
    received_count = ft.Text("", size=13)

    new_order_btn = ft.ElevatedButton(
        i18n.t("warehouse.orders.new_order_button"),
        icon=ft.Icons.ADD,
        on_click=lambda e: _open_new_order_dialog(
            page, controller, load_data, _highest_id, _products, _raw_materials
        ),
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
        nonlocal orders, _products, _raw_materials, _highest_id
        try:
            loading.visible = True
            page.update()

            orders = await controller.get_replenishment_history()
            _highest_id = max((o.id for o in orders), default=0)

            _products = await controller.get_products()
            _raw_materials = await controller.get_raw_materials()

            pending_table.rows.clear()
            received_table.rows.clear()
            pending_orders = []
            received_orders = []
            for o in orders:
                is_received = o.id in RECEIVED_ORDER_IDS or (
                    o.status and o.status in ("RECEIVED", "COMPLETED")
                )
                lines_text = format_lines(o.lines)
                created = o.createdAt.strftime("%Y-%m-%d %H:%M") if o.createdAt else "-"

                if is_received:
                    action_btn = ft.Container(
                        content=ft.Text(
                            i18n.t("warehouse.orders.received_badge"),
                            color=ft.Colors.GREEN,
                            weight=ft.FontWeight.BOLD,
                            size=13,
                        ),
                    )
                    received_orders.append(o)
                else:
                    action_btn = ft.ElevatedButton(
                        i18n.t("warehouse.orders.mark_received"),
                        on_click=lambda _, oid=o.id: page.run_task(
                            _mark_received, page, controller, oid, load_data
                        ),
                        height=36,
                        style=ft.ButtonStyle(padding=ft.Padding(8, 4, 8, 4)),
                    )
                    pending_orders.append(o)

                target = received_table if is_received else pending_table
                target.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(o.id))),
                            ft.DataCell(ft.Text(o.status or "PENDING")),
                            ft.DataCell(ft.Text(o.note or "-")),
                            ft.DataCell(ft.Text(created)),
                            ft.DataCell(
                                ft.Container(
                                    content=ft.Text(
                                        lines_text,
                                        size=12,
                                        max_lines=2,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
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

            pending_count.value = f"{len(pending_orders)} w trakcie"
            received_count.value = f"{len(received_orders)} odebrane"

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
        content=ft.ListView(
            expand=True,
            spacing=15,
            controls=[
                ft.Text(
                    i18n.t("warehouse.orders_title"),
                    size=24,
                    weight=ft.FontWeight.BOLD,
                ),
                new_order_btn,
                loading,
                ft.Text("W trakcie", size=18, weight=ft.FontWeight.BOLD),
                pending_count,
                pending_table,
                ft.Divider(),
                ft.Text("Odebrane", size=18, weight=ft.FontWeight.BOLD),
                received_count,
                received_table,
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
    _highest_id: int = 0,
    _products: list | None = None,
    _raw_materials: list | None = None,
):
    has_raw_materials = bool(_raw_materials)
    line_rows: list[dict] = []
    is_submitting = False
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
            type_dd = row_data["type_dd"]
            pid_field = row_data["id_field"]
            qty_field = row_data["qty"]
            pick_btn = row_data["pick_btn"]

            line_row = ft.Row(
                controls=[
                    ft.Text(str(idx + 1) + ".", width=25),
                    type_dd,
                    pid_field,
                    pick_btn,
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

    def _show_product_picker(pid_field):
        def pick_product(e, product_id):
            pid_field.value = str(product_id)
            picker_dlg.open = False
            page.update()

        product_controls = [
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(str(p.productId), weight=ft.FontWeight.BOLD, width=40),
                        ft.Text(p.name, expand=True),
                    ]
                ),
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                on_click=lambda _, pid=p.productId: pick_product(_, pid),
            )
            for p in (_products or [])
        ]

        picker_dlg = ft.AlertDialog(
            title=ft.Text(
                i18n.t("warehouse.orders.product"),
                size=18,
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Column(
                controls=product_controls,
                scroll=ft.ScrollMode.AUTO,
                width=400,
                height=450,
                spacing=2,
            ),
            actions=[
                ft.TextButton(
                    i18n.t("warehouse.orders.cancel"),
                    on_click=lambda e: (
                        setattr(picker_dlg, "open", False) or page.update()
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(picker_dlg)
        picker_dlg.open = True
        page.update()

    def _show_raw_material_picker(rm_field):
        def pick_raw_material(e, material_id):
            rm_field.value = str(material_id)
            picker_dlg.open = False
            page.update()

        material_controls = [
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(str(m.id), weight=ft.FontWeight.BOLD, width=40),
                        ft.Text(m.name, expand=True),
                        ft.Text(m.unit, width=40),
                    ]
                ),
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                on_click=lambda _, mid=m.id: pick_raw_material(_, mid),
            )
            for m in (_raw_materials or [])
        ]

        picker_dlg = ft.AlertDialog(
            title=ft.Text(
                i18n.t("warehouse.orders.pick_raw_material"),
                size=18,
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Column(
                controls=material_controls,
                scroll=ft.ScrollMode.AUTO,
                width=400,
                height=450,
                spacing=2,
            ),
            actions=[
                ft.TextButton(
                    i18n.t("warehouse.orders.cancel"),
                    on_click=lambda e: (
                        setattr(picker_dlg, "open", False) or page.update()
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(picker_dlg)
        picker_dlg.open = True
        page.update()

    def add_line(e):
        row_data: dict = {}

        type_options = [
            ft.dropdown.Option("product", i18n.t("warehouse.orders.product")),
        ]
        if has_raw_materials:
            type_options.append(
                ft.dropdown.Option(
                    "raw_material", i18n.t("warehouse.orders.raw_material")
                )
            )
        type_dd = ft.Dropdown(
            options=type_options,
            value="product",
            width=120,
            text_size=13,
        )
        pid = ft.TextField(
            label="ID",
            width=80,
            input_filter=ft.InputFilter(allow=True, regex_string=r"^[0-9]*$"),
            keyboard_type=ft.KeyboardType.NUMBER,
            text_size=14,
        )
        pick_btn = ft.IconButton(
            icon=ft.Icons.SEARCH,
            icon_size=20,
            tooltip="Wybierz produkt",
        )
        qty = ft.TextField(
            label=i18n.t("warehouse.orders.quantity_delta"),
            width=130,
            input_filter=ft.InputFilter(allow=True, regex_string=r"^-?[0-9]*$"),
            keyboard_type=ft.KeyboardType.NUMBER,
            text_size=14,
        )

        def on_type_change(e):
            row_data["type"] = e.control.value
            if row_data["type"] == "product":
                pid.label = "ID"
                pick_btn.tooltip = i18n.t("warehouse.orders.product")
            else:
                pid.label = i18n.t("warehouse.orders.raw_material_id")
                pick_btn.tooltip = i18n.t("warehouse.orders.pick_raw_material")
            page.update()

        def on_pick(e):
            if row_data["type"] == "product":
                _show_product_picker(pid)
            else:
                _show_raw_material_picker(pid)

        type_dd.on_change = on_type_change
        pick_btn.on_click = on_pick

        row_data["type"] = "product"
        row_data["type_dd"] = type_dd
        row_data["id_field"] = pid
        row_data["pick_btn"] = pick_btn
        row_data["qty"] = qty
        line_rows.append(row_data)
        rebuild_lines()

    async def submit_order(e):
        nonlocal is_submitting
        if is_submitting or not line_rows:
            status_text.value = i18n.t("warehouse.enter_product_id")
            status_text.color = ft.Colors.RED
            status_text.visible = True
            page.update()
            return

        is_submitting = True
        submit_btn.disabled = True
        page.update()

        note = note_field.value.strip() if note_field.value else None
        lines = []

        for row_data in line_rows:
            id_val = row_data["id_field"].value
            qty_val = row_data["qty"].value
            if not id_val or not qty_val:
                continue
            try:
                parsed_id = int(id_val)
                parsed_qty = int(qty_val)
                if row_data["type"] == "product":
                    lines.append({"productId": parsed_id, "quantityDelta": parsed_qty})
                else:
                    lines.append(
                        {"rawMaterialId": parsed_id, "quantityDelta": parsed_qty}
                    )
            except ValueError:
                continue

        if not lines:
            is_submitting = False
            submit_btn.disabled = False
            status_text.value = i18n.t("warehouse.enter_product_id")
            status_text.color = ft.Colors.RED
            status_text.visible = True
            page.update()
            return

        result = await controller.create_replenishment(lines, note)

        dlg.open = False
        page.update()

        if result is not None:
            _show_snack(
                page,
                i18n.t("warehouse.orders.create_success"),
            )
        else:
            if not connectivity_service.is_online():
                _show_snack(
                    page,
                    i18n.t("offline.queued"),
                    is_warning=True,
                )
            else:
                _show_snack(
                    page,
                    i18n.t("warehouse.orders.create_fail"),
                    is_error=True,
                )

        await reload_callback()

    add_line(None)

    submit_btn = ft.ElevatedButton(
        i18n.t("warehouse.orders.create_button"),
        on_click=lambda e: page.run_task(submit_order, e),
    )

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text(
            i18n.t("warehouse.orders.create_title"),
            size=20,
            weight=ft.FontWeight.BOLD,
        ),
        content=ft.Column(
            width=600,
            height=400,
            controls=[
                *(
                    [
                        ft.Text(
                            i18n.t("warehouse.no_raw_materials"),
                            size=12,
                            color=ft.Colors.AMBER,
                        )
                    ]
                    if not has_raw_materials
                    else []
                ),
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
            submit_btn,
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
    elif not connectivity_service.is_online():
        _show_snack(page, i18n.t("offline.queued"), is_warning=True)
    else:
        _show_snack(page, i18n.t("warehouse.orders.received_fail"), is_error=True)
    await reload_callback()
