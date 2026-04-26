import flet as ft
from desktop_alkozon.features.employees.controller import EmployeesController
from desktop_alkozon.core.auth import auth_service


def create_employees_view(page: ft.Page) -> ft.Container:
    controller = EmployeesController()
    offers = []
    employees = []

    offers_table = ft.DataTable(columns=[
        ft.DataColumn(ft.Text("ID")),
        ft.DataColumn(ft.Text("Oferta")),
        ft.DataColumn(ft.Text("Wynagrodzenie")),
        ft.DataColumn(ft.Text("Status")),
    ], rows=[])

    employees_table = ft.DataTable(columns=[
        ft.DataColumn(ft.Text("ID")),
        ft.DataColumn(ft.Text("Imię i nazwisko")),
        ft.DataColumn(ft.Text("Stanowisko")),
        ft.DataColumn(ft.Text("Status")),
    ], rows=[])

    loading = ft.ProgressRing(visible=False)

    title_field = ft.TextField(label="Tytuł oferty", width=300, max_length=100)
    description_field = ft.TextField(label="Opis oferty", width=400, max_length=500, multiline=True, min_lines=2)
    salary_field = ft.TextField(label="Wynagrodzenie", width=150, max_length=10,
                                 input_filter=ft.InputFilter(allow=True, regex_string=r"^\d*\.?\d*$"),
                                 keyboard_type=ft.KeyboardType.NUMBER)

    def refresh_tables():
        nonlocal offers, employees
        offers_table.rows.clear()
        for o in offers:
            salary_str = f"{o.salary:.2f} zł" if o.salary else "Do ustalenia"
            offers_table.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(o.id))),
                ft.DataCell(ft.Text(o.title)),
                ft.DataCell(ft.Text(salary_str)),
                ft.DataCell(ft.Text(o.status)),
            ]))

        employees_table.rows.clear()
        for e in employees:
            employees_table.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(e.id))),
                ft.DataCell(ft.Text(e.name)),
                ft.DataCell(ft.Text(e.position)),
                ft.DataCell(ft.Text(e.status)),
            ]))

    async def load_data():
        nonlocal offers, employees
        try:
            loading.visible = True
            page.update()

            offers = await controller.get_offers()
            employees = await controller.get_employees()
            refresh_tables()

            loading.visible = False
            page.update()
        except Exception as e:
            print(f"Error loading employees data: {e}")
            offers = controller.get_offers_sync()
            employees = controller.get_employees_sync()
            refresh_tables()
            loading.visible = False
            page.update()

    async def create_offer_async(title, description, salary):
        await controller.create_offer(title, description, salary)
        await load_data()

    def post_offer_clicked(e):
        auth_service.update_activity()
        if not title_field.value or not title_field.value.strip():
            snack = ft.SnackBar(content=ft.Text("Wypełnij tytuł oferty"), duration=2000)
            page.overlay.append(snack)
            snack.open = True
            page.update()
            return

        salary = None
        if salary_field.value and salary_field.value.strip():
            try:
                salary = float(salary_field.value)
            except ValueError:
                snack = ft.SnackBar(content=ft.Text("Nieprawidłowa kwota wynagrodzenia"), duration=2000)
                page.overlay.append(snack)
                snack.open = True
                page.update()
                return

        page.run_task(create_offer_async, title_field.value.strip(), description_field.value.strip() if description_field.value else "", salary)
        
        title_field.value = ""
        description_field.value = ""
        salary_field.value = ""

        snack = ft.SnackBar(content=ft.Text("Nowa oferta wystawiona"), duration=2000)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def go_to_menu(e):
        from desktop_alkozon.ui.pages.login_page import create_main_menu_view
        page.clean()
        page.add(create_main_menu_view(page))
        page.update()

    form = ft.Column(controls=[
        ft.Text("Nowa oferta pracy", size=16, weight=ft.FontWeight.BOLD),
        ft.Row(controls=[title_field, salary_field]),
        description_field,
        ft.ElevatedButton("Wystaw nową ofertę", on_click=post_offer_clicked),
    ], spacing=10)

    content = ft.Column(controls=[
        ft.Text("Pracownicy i oferty pracy", size=24, weight=ft.FontWeight.BOLD),
        ft.Text("Aktualne oferty pracy", size=18),
        ft.Row([loading, offers_table]),
        ft.Divider(),
        ft.Text("Zatrudnieni pracownicy", size=18),
        employees_table,
        ft.Divider(),
        form,
        ft.ElevatedButton("Powrót do menu głównego", width=400, on_click=go_to_menu),
    ], spacing=15)

    page.run_task(load_data)

    return ft.Container(
        padding=20,
        content=content,
    )
