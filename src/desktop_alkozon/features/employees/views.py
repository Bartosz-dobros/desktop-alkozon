import flet as ft
from desktop_alkozon.features.employees.controller import EmployeesController
from desktop_alkozon.core.auth import auth_service

class EmployeesView(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(padding=20)
        self._page = page
        self.controller = EmployeesController()

        self.offers_table = ft.DataTable(columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Oferta")),
            ft.DataColumn(ft.Text("Wynagrodzenie")),
            ft.DataColumn(ft.Text("Status")),
        ], rows=[])

        self.employees_table = ft.DataTable(columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Imię i nazwisko")),
            ft.DataColumn(ft.Text("Stanowisko")),
            ft.DataColumn(ft.Text("Status")),
        ], rows=[])

        self.title_field = ft.TextField(label="Tytuł oferty", width=300, max_length=100)
        self.salary_field = ft.TextField(label="Wynagrodzenie", width=150, max_length=10,
                                         input_filter=ft.InputFilter(allow=True, regex_string=r"^\d*\.?\d*$"))

        self.form = ft.Row(controls=[
            self.title_field,
            self.salary_field,
            ft.ElevatedButton("Wystaw nową ofertę", on_click=self.post_offer_clicked),
        ], spacing=10)

        self.content = ft.Column(controls=[
            ft.Text("Pracownicy i oferty pracy", size=24, weight=ft.FontWeight.BOLD),
            ft.Text("Aktualne oferty pracy", size=18),
            self.offers_table,
            ft.Divider(),
            ft.Text("Zatrudnieni pracownicy", size=18),
            self.employees_table,
            ft.Divider(),
            ft.Text("Nowa oferta pracy", size=18, weight=ft.FontWeight.BOLD),
            self.form,
            ft.ElevatedButton("Powrót do menu głównego", width=400, on_click=self._go_to_menu),
        ], spacing=15)

        self.refresh_tables()

    def refresh_tables(self):
        self.offers_table.rows.clear()
        for o in self.controller.get_offers():
            self.offers_table.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(o.id))),
                ft.DataCell(ft.Text(o.title)),
                ft.DataCell(ft.Text(f"{o.salary:.2f} zł")),
                ft.DataCell(ft.Text(o.status)),
            ]))

        self.employees_table.rows.clear()
        for e in self.controller.get_employees():
            self.employees_table.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(e.id))),
                ft.DataCell(ft.Text(e.name)),
                ft.DataCell(ft.Text(e.position)),
                ft.DataCell(ft.Text(e.status)),
            ]))
        self._page.update()

    def post_offer_clicked(self, e):
        if not (self.title_field.value and self.salary_field.value):
            auth_service.update_activity()
            snack = ft.SnackBar(content=ft.Text("Wypełnij wszystkie pola"), duration=2000)
            self._page.overlay.append(snack)
            snack.open = True
            self._page.update()
            return

        self.controller.create_offer(self.title_field.value.strip(), float(self.salary_field.value))
        self.refresh_tables()
        self.title_field.value = ""
        self.salary_field.value = ""

        snack = ft.SnackBar(content=ft.Text("Nowa oferta wystawiona"), duration=2000)
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def _go_to_menu(self, e):
        from desktop_alkozon.ui.pages.main_menu import MainMenuView
        self._page.clean()
        self._page.add(MainMenuView(self._page))
        self._page.update()