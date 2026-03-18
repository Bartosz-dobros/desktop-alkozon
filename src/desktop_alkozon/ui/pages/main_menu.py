import flet as ft

class MainMenuView(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(padding=40, alignment=ft.Alignment(0.5, 0.5))
        self._page = page

        self.content = ft.Column(
            controls=[
                ft.Text("AlkozOn Desktop", size=32, weight=ft.FontWeight.BOLD),
                ft.Text("Wybierz sekcję", size=20),
                ft.Divider(),
                ft.ElevatedButton(
                    "Stan magazynu i zamówienia",
                    width=500,
                    height=60,
                    on_click=self._go_to_warehouse,
                ),
                ft.ElevatedButton(
                    "Kurierzy i dostawy",
                    width=500,
                    height=60,
                    on_click=self._go_to_deliveries,
                ),
                ft.ElevatedButton(
                    "Pracownicy (oferty pracy)",
                    width=500,
                    height=60,
                    on_click=lambda e: self._page.show_snack_bar(
                        ft.SnackBar(ft.Text("Employees feature to do"), duration=2000)
                    ),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15,
        )

    def _go_to_warehouse(self, e):
        from desktop_alkozon.features.warehouse.views import WarehouseView
        self._page.clean()
        self._page.add(WarehouseView(self._page))
        self._page.update()

    def _go_to_deliveries(self, e):
        from desktop_alkozon.features.deliveries.views import DeliveriesView
        self._page.clean()
        self._page.add(DeliveriesView(self._page))
        self._page.update()