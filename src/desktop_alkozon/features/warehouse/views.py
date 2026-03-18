import flet as ft
from desktop_alkozon.features.warehouse.controller import WarehouseController

class WarehouseView(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(padding=20)
        self._page = page
        self.controller = WarehouseController()

        self.table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Nazwa towaru")),
                ft.DataColumn(ft.Text("Ilość")),
                ft.DataColumn(ft.Text("Jednostka")),
                ft.DataColumn(ft.Text("Cena")),
            ],
            rows=[],
        )

        self.name_field = ft.TextField(
            label="Nazwa towaru",
            width=300,
            max_length=100,
            text_size=14,
        )
        self.quantity_field = ft.TextField(
            label="Ilość",
            width=120,
            max_length=5,
            input_filter=ft.InputFilter(allow=True, regex_string=r"^[0-9]*$"),
            keyboard_type=ft.KeyboardType.NUMBER,
            text_size=14,
        )
        self.unit_field = ft.TextField(
            label="Jednostka",
            width=100,
            value="szt.",
            max_length=10,
            text_size=14,
        )
        self.price_field = ft.TextField(
            label="Cena",
            width=120,
            max_length=10,
            input_filter=ft.InputFilter(allow=True, regex_string=r"^\d*\.?\d*$"),
            keyboard_type=ft.KeyboardType.NUMBER,
            text_size=14,
        )

        self.form = ft.Row(
            controls=[
                self.name_field,
                self.quantity_field,
                self.unit_field,
                self.price_field,
                ft.ElevatedButton("Zamów nowy towar", on_click=self.add_item_clicked),
            ],
            spacing=10,
        )

        self.content = ft.Column(
            controls=[
                ft.Text("Stan magazynu", size=24, weight=ft.FontWeight.BOLD),
                self.table,
                ft.Divider(),
                ft.Text("Zamów nowy towar", size=18, weight=ft.FontWeight.BOLD),
                self.form,
                ft.ElevatedButton(
                    "Powrót do menu głównego",
                    width=400,
                    on_click=self._go_to_menu,
                ),
            ],
            spacing=20,
        )

        self.refresh_table()

    def refresh_table(self):
        self.table.rows.clear()
        for item in self.controller.get_stock_data():
            self.table.rows.append(
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
        self._page.update()

    def add_item_clicked(self, e):
        if not (self.name_field.value and self.name_field.value.strip() and
                self.quantity_field.value and self.quantity_field.value.strip() and
                self.unit_field.value and self.unit_field.value.strip() and
                self.price_field.value and self.price_field.value.strip()):
            snack = ft.SnackBar(
                content=ft.Text("Wszystkie pola muszą być wypełnione"),
                duration=2000,
                action="OK"
            )
            self._page.overlay.append(snack)
            snack.open = True
            self._page.update()
            return

        try:
            self.controller.order_new_item(
                self.name_field.value.strip(),
                int(self.quantity_field.value),
                self.unit_field.value.strip(),
                float(self.price_field.value),
            )
            self.refresh_table()
            self.name_field.value = ""
            self.quantity_field.value = ""
            self.unit_field.value = "szt."
            self.price_field.value = ""

            snack = ft.SnackBar(
                content=ft.Text("Nowy towar dodany do magazynu"),
                duration=2000,
                action="OK"
            )
            self._page.overlay.append(snack)
            snack.open = True
            self._page.update()
        except ValueError:
            snack = ft.SnackBar(
                content=ft.Text("Wypełnij poprawnie wszystkie pola"),
                duration=2000,
                action="OK"
            )
            self._page.overlay.append(snack)
            snack.open = True
            self._page.update()

    def _go_to_menu(self, e):
        from desktop_alkozon.ui.pages.main_menu import MainMenuView
        self._page.clean()
        self._page.add(MainMenuView(self._page))
        self._page.update()