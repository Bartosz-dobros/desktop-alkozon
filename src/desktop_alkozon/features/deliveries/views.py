import flet as ft

from desktop_alkozon.core.auth import auth_service
from desktop_alkozon.features.deliveries.controller import DeliveriesController


def create_deliveries_view(page: ft.Page) -> ft.Container:
    controller = DeliveriesController()
    deliveries = []
    unassigned_couriers = []
    selected_delivery_id = None

    deliveries_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Zamowienie")),
            ft.DataColumn(ft.Text("Adres")),
            ft.DataColumn(ft.Text("Status")),
            ft.DataColumn(ft.Text("Wybierz")),
        ],
        rows=[],
    )

    couriers_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Email")),
            ft.DataColumn(ft.Text("Akcja")),
        ],
        rows=[],
    )

    loading = ft.ProgressRing(visible=False)
    selected_delivery_text = ft.Text("Zadna dostawa nie jest wybrana", size=14)

    def refresh_tables():
        nonlocal deliveries, unassigned_couriers
        deliveries_table.rows.clear()
        if deliveries:
            for d in deliveries:
                select_btn = ft.IconButton(
                    icon=ft.icons.Icons.ADS_CLICK,
                    icon_color=ft.Colors.BLUE_400,
                    on_click=lambda e, did=d.id: select_delivery(did),
                )
                deliveries_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(d.id))),
                            ft.DataCell(ft.Text(str(d.orderId))),
                            ft.DataCell(ft.Text(d.addressSnapshot)),
                            ft.DataCell(
                                ft.Text(
                                    d.status.value
                                    if hasattr(d.status, "value")
                                    else str(d.status)
                                )
                            ),
                            ft.DataCell(select_btn),
                        ]
                    )
                )

        def make_assign_handler(courier_id: int):
            def handler(e):
                assign_courier_to_delivery(selected_delivery_id, courier_id)

            return handler

        couriers_table.rows.clear()
        if unassigned_couriers:
            for c in unassigned_couriers:
                assign_btn = ft.ElevatedButton(
                    "Przypisz",
                    on_click=make_assign_handler(c.get("id")),
                )
                couriers_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(c.get("id", "")))),
                            ft.DataCell(ft.Text(c.get("email", ""))),
                            ft.DataCell(assign_btn),
                        ]
                    )
                )

    def show_error(message: str):
        snack = ft.SnackBar(
            content=ft.Text(message), duration=3000, bgcolor=ft.Colors.RED_800
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def show_success(message: str):
        snack = ft.SnackBar(
            content=ft.Text(message), duration=2000, bgcolor=ft.Colors.GREEN_800
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def select_delivery(delivery_id: int):
        nonlocal selected_delivery_id
        selected_delivery_id = delivery_id
        selected_delivery_text.value = f"Wybrana dostawa: ID {delivery_id}"
        page.update()

    async def load_data():
        nonlocal deliveries, unassigned_couriers, selected_delivery_id
        try:
            loading.visible = True
            page.update()

            deliveries = await controller.get_deliveries(status="PENDING") or []
            unassigned_couriers = await controller.get_unassigned_couriers() or []
            refresh_tables()

            loading.visible = False
            page.update()
        except Exception as e:
            print(f"Error loading deliveries data: {e}")
            deliveries = controller.get_deliveries_sync() or []
            unassigned_couriers = controller.get_unassigned_couriers_sync() or []
            refresh_tables()
            loading.visible = False
            show_error("Failed to load deliveries data. Please try again.")

    async def assign_courier_to_delivery_async(delivery_id: int, courier_id: int):
        result = await controller.assign_courier(delivery_id, courier_id)
        if result:
            show_success(f"Kurier przypisany do dostawy {delivery_id}")
        else:
            show_error(f"Nie udalo sie przypisac kuriera do dostawy {delivery_id}")
        await load_data()

    def assign_courier_to_delivery(delivery_id: int, courier_id: int):
        auth_service.update_activity()
        if delivery_id is None:
            show_error("Najpierw wybierz dostawe z listy")
            return
        if courier_id is None:
            show_error("Niepoprawny identyfikator kuriera")
            return
        page.run_task(assign_courier_to_delivery_async, delivery_id, courier_id)

    def go_to_menu(e):
        from desktop_alkozon.ui.pages.login_page import create_main_menu_view

        page.clean()
        page.add(create_main_menu_view(page))
        page.update()

    content = ft.Column(
        controls=[
            ft.Text("Kurierzy i stan dostaw", size=24, weight=ft.FontWeight.BOLD),
            loading,
            ft.Divider(),
            ft.Text("Oczekujace dostawy", size=18, weight=ft.FontWeight.BOLD),
            ft.Text(
                "Dostawy o statusie PENDING oczekujace na przypisanie kuriera", size=13
            ),
            deliveries_table,
            ft.Divider(),
            ft.Text("Dostepni kurierzy", size=18, weight=ft.FontWeight.BOLD),
            ft.Text("Kurierzy nieprzypisani do zadnej dostawy", size=13),
            couriers_table,
            ft.Divider(),
            selected_delivery_text,
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

    return ft.Container(
        padding=20,
        content=content,
    )
