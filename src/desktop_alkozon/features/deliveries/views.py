import flet as ft
from desktop_alkozon.features.deliveries.controller import DeliveriesController

class DeliveriesView(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(padding=20)
        self._page = page
        self.controller = DeliveriesController()

        self.couriers_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Kurier")),
                ft.DataColumn(ft.Text("Status")),
                ft.DataColumn(ft.Text("Pojazd")),
            ],
            rows=[],
        )

        self.deliveries_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Kurier")),
                ft.DataColumn(ft.Text("Cel")),
                ft.DataColumn(ft.Text("Status")),
                ft.DataColumn(ft.Text("Ogłoszenie")),
            ],
            rows=[],
        )

        self.courier_dropdown = ft.Dropdown(
            label="Wybierz kuriera",
            width=250,
            options=[ft.dropdown.Option(c.name) for c in self.controller.get_couriers()]
        )
        self.destination_field = ft.TextField(
            label="Cel dostawy",
            width=250,
            max_length=150,
            text_size=14,
        )
        self.announcement_field = ft.TextField(
            label="Treść ogłoszenia",
            width=400,
            multiline=True,
            min_lines=2,
            max_length=500,
            text_size=14,
        )

        self.form = ft.Column(
            controls=[
                self.courier_dropdown,
                self.destination_field,
                self.announcement_field,
                ft.ElevatedButton("Utwórz ogłoszenie dostawy", on_click=self.create_announcement_clicked),
            ],
            spacing=10,
        )

        self.content = ft.Column(
            controls=[
                ft.Text("Kurierzy i stan dostaw", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("Dostępni kurierzy", size=18),
                self.couriers_table,
                ft.Divider(),
                ft.Text("Aktualne dostawy", size=18),
                self.deliveries_table,
                ft.Divider(),
                ft.Text("Nowe ogłoszenie dostawy", size=18, weight=ft.FontWeight.BOLD),
                self.form,
                ft.ElevatedButton(
                    "Powrót do menu głównego",
                    width=400,
                    on_click=self._go_to_menu,
                ),
            ],
            spacing=15,
        )

        self.refresh_tables()

    def refresh_tables(self):
        self.couriers_table.rows.clear()
        for c in self.controller.get_couriers():
            self.couriers_table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(c.id))),
                    ft.DataCell(ft.Text(c.name)),
                    ft.DataCell(ft.Text(c.status)),
                    ft.DataCell(ft.Text(c.vehicle)),
                ])
            )

        self.deliveries_table.rows.clear()
        for d in self.controller.get_deliveries():
            self.deliveries_table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(d.id))),
                    ft.DataCell(ft.Text(d.courier_name)),
                    ft.DataCell(ft.Text(d.destination)),
                    ft.DataCell(ft.Text(d.status)),
                    ft.DataCell(ft.Text(d.announcement)),
                ])
            )
        self._page.update()

    def create_announcement_clicked(self, e):
        if not (self.courier_dropdown.value and self.destination_field.value.strip() and self.announcement_field.value.strip()):
            snack = ft.SnackBar(content=ft.Text("Wypełnij wszystkie pola"), duration=2000)
            self._page.overlay.append(snack)
            snack.open = True
            self._page.update()
            return

        self.controller.create_new_announcement(
            self.courier_dropdown.value,
            self.destination_field.value.strip(),
            self.announcement_field.value.strip()
        )
        self.refresh_tables()

        self.destination_field.value = ""
        self.announcement_field.value = ""
        snack = ft.SnackBar(content=ft.Text("Ogłoszenie dostawy utworzone"), duration=2000)
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def _go_to_menu(self, e):
        from desktop_alkozon.ui.pages.main_menu import MainMenuView
        self._page.clean()
        self._page.add(MainMenuView(self._page))
        self._page.update()