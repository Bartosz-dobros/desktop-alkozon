import flet as ft

from desktop_alkozon.core.auth import auth_service
from desktop_alkozon.features.employees.controller import EmployeesController


def create_employees_view(page: ft.Page) -> ft.Container:
    def go_to_employee_list(e):
        auth_service.update_activity()
        page.clean()
        page.add(create_employee_list_view(page))
        page.update()

    def go_to_job_offers(e):
        auth_service.update_activity()
        page.clean()
        page.add(create_job_offers_view(page))
        page.update()

    def go_to_menu(e):
        from desktop_alkozon.ui.pages.login_page import create_main_menu_view

        page.clean()
        page.add(create_main_menu_view(page))
        page.update()

    content = ft.Column(
        controls=[
            ft.Text("Pracownicy i oferty pracy", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.ElevatedButton(
                "Lista pracownikow",
                width=500,
                height=60,
                on_click=go_to_employee_list,
            ),
            ft.ElevatedButton(
                "Oferty pracy",
                width=500,
                height=60,
                on_click=go_to_job_offers,
            ),
            ft.Divider(),
            ft.ElevatedButton(
                "Powrot do menu glownego",
                width=400,
                on_click=go_to_menu,
            ),
        ],
        spacing=15,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    return ft.Container(
        padding=20,
        alignment=ft.Alignment(0.5, 0.5),
        content=content,
    )


def _make_group_section(label: str) -> dict:
    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Email")),
            ft.DataColumn(ft.Text("Status")),
            ft.DataColumn(ft.Text("Kurier")),
        ],
        rows=[],
    )
    count_text = ft.Text(f"0 {label.lower()}", size=12, color=ft.Colors.GREY_400)
    section = ft.Column(
        controls=[
            ft.Text(label, size=16, weight=ft.FontWeight.BOLD),
            count_text,
            table,
            ft.Divider(height=1),
        ],
        spacing=4,
    )
    return {
        "section": section,
        "table": table,
        "count_text": count_text,
        "label": label,
    }


def create_employee_list_view(page: ft.Page) -> ft.Container:
    controller = EmployeesController()
    employees = []

    mgr = _make_group_section("Managerowie")
    emp = _make_group_section("Pracownicy")
    cou = _make_group_section("Kurierzy")

    loading = ft.ProgressRing(visible=False)

    email_field = ft.TextField(
        label="Email",
        width=300,
        keyboard_type=ft.KeyboardType.EMAIL,
        max_length=100,
    )
    password_field = ft.TextField(
        label="Haslo",
        password=True,
        can_reveal_password=True,
        width=300,
        max_length=128,
    )
    confirm_password_field = ft.TextField(
        label="Potwierdz haslo",
        password=True,
        can_reveal_password=True,
        width=300,
        max_length=128,
    )
    first_name_field = ft.TextField(
        label="Imie (opcjonalnie)",
        width=300,
        max_length=50,
    )
    last_name_field = ft.TextField(
        label="Nazwisko (opcjonalnie)",
        width=300,
        max_length=50,
    )
    courier_switch = ft.Switch(label="Kurier", value=False)
    role_dropdown = ft.Dropdown(
        label="Rola",
        width=300,
        options=[
            ft.dropdown.Option("EMPLOYEE", "Pracownik"),
            ft.dropdown.Option("MANAGER", "Manager"),
        ],
        value="EMPLOYEE",
    )

    def refresh_groups():
        def fill_group(info, subset):
            info["table"].rows.clear()
            for e in subset:
                status_str = "Aktywny" if e.active else "Nieaktywny"
                courier_str = "Tak" if e.courier else "Nie"
                info["table"].rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(e.id))),
                            ft.DataCell(ft.Text(e.email)),
                            ft.DataCell(ft.Text(status_str)),
                            ft.DataCell(ft.Text(courier_str)),
                        ]
                    )
                )
            info["count_text"].value = f"{len(subset)} {info['label'].lower()}"

        managers = [e for e in employees if e.role == "MANAGER"]
        regular = [e for e in employees if e.role == "EMPLOYEE" and not e.courier]
        couriers_list = [e for e in employees if e.role == "EMPLOYEE" and e.courier]

        fill_group(mgr, managers)
        fill_group(emp, regular)
        fill_group(cou, couriers_list)

        page.update()

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
            duration=4000,
            bgcolor=ft.Colors.GREEN_800,
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    async def load_employees():
        nonlocal employees
        try:
            loading.visible = True
            page.update()

            employees = await controller.get_employees() or []
            refresh_groups()

            loading.visible = False
            page.update()
        except Exception as e:
            print(f"Error loading employees: {e}")
            employees = controller.get_employees_sync() or []
            refresh_groups()
            loading.visible = False
            show_error("Nie udalo sie zaladowac listy pracownikow.")

    async def create_employee_async():
        nonlocal employees

        email = email_field.value.strip() if email_field.value else ""
        password = password_field.value if password_field.value else ""
        confirm = confirm_password_field.value if confirm_password_field.value else ""
        first_name = first_name_field.value.strip() if first_name_field.value else ""
        last_name = last_name_field.value.strip() if last_name_field.value else ""
        courier = courier_switch.value
        role = role_dropdown.value

        if not email:
            show_error("Email jest wymagany.")
            return
        if not password or len(password) < 8:
            show_error("Haslo musi miec co najmniej 8 znakow.")
            return
        if password != confirm:
            show_error("Hasla nie sa zgodne.")
            return

        try:
            loading.visible = True
            page.update()

            result = await controller.create_employee_account(
                email, password, first_name, last_name, courier, role
            )
            if result:
                show_success(
                    f"Konto pracownika utworzone: {result.email}. "
                    "Kod 2FA zostanie wyslany przy pierwszym logowaniu."
                )
                email_field.value = ""
                password_field.value = ""
                confirm_password_field.value = ""
                first_name_field.value = ""
                last_name_field.value = ""
                courier_switch.value = False
                role_dropdown.value = "EMPLOYEE"
                employees = await controller.get_employees() or []
                refresh_groups()
            else:
                show_error("Nie udalo sie utworzyc konta pracownika.")

            loading.visible = False
            page.update()
        except Exception as e:
            print(f"Error creating employee: {e}")
            loading.visible = False
            show_error("Blad podczas tworzenia konta pracownika.")

    def create_employee_clicked(e):
        auth_service.update_activity()
        page.run_task(create_employee_async)

    def go_back(e):
        auth_service.update_activity()
        page.clean()
        page.add(create_employees_view(page))
        page.update()

    content = ft.Column(
        controls=[
            ft.Text("Lista pracownikow", size=24, weight=ft.FontWeight.BOLD),
            ft.Row([loading]),
            mgr["section"],
            emp["section"],
            cou["section"],
            ft.Divider(),
            ft.Text("Dodaj nowego pracownika", size=18, weight=ft.FontWeight.BOLD),
            email_field,
            password_field,
            confirm_password_field,
            first_name_field,
            last_name_field,
            role_dropdown,
            courier_switch,
            ft.ElevatedButton(
                "Utworz konto pracownika", on_click=create_employee_clicked
            ),
            ft.Divider(),
            ft.ElevatedButton(
                "Powrot do menu pracownikow",
                width=400,
                on_click=go_back,
            ),
        ],
        spacing=10,
        scroll=ft.ScrollMode.AUTO,
    )

    page.run_task(load_employees)

    container = ft.Container(
        padding=20,
        content=content,
    )
    container.controls = content.controls
    return container


def create_job_offers_view(page: ft.Page) -> ft.Container:
    controller = EmployeesController()
    offers = []

    def _make_offer_section(label: str, show_actions: bool = False) -> dict:
        cols = [
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Oferta")),
            ft.DataColumn(ft.Text("Opis")),
        ]
        if show_actions:
            cols.append(ft.DataColumn(ft.Text("Akcje")))
        table = ft.DataTable(columns=cols, rows=[])
        count = ft.Text(f"0 {label.lower()}", size=12, color=ft.Colors.GREY_400)
        section = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(label, size=16, weight=ft.FontWeight.BOLD),
                        count,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                table,
                ft.Divider(height=1),
            ],
            spacing=4,
        )
        return {"table": table, "count": count, "section": section, "label": label}

    open_group = _make_offer_section("Otwarte", show_actions=True)
    closed_group = _make_offer_section("Zamkniete")

    loading = ft.ProgressRing(visible=False)

    title_field = ft.TextField(label="Tytul oferty", width=300, max_length=100)
    description_field = ft.TextField(
        label="Opis oferty",
        width=400,
        max_length=500,
        multiline=True,
        min_lines=2,
    )

    def refresh_sections():
        def fill(info, subset, with_actions=False):
            info["table"].rows.clear()
            for o in subset:
                desc = o.description or ""
                cells = [
                    ft.DataCell(ft.Text(str(o.id))),
                    ft.DataCell(ft.Text(o.title)),
                    ft.DataCell(ft.Text(desc[:50] + "..." if len(desc) > 50 else desc)),
                ]
                if with_actions:
                    close_btn = ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_size=18,
                        tooltip="Zamknij oferte",
                        on_click=lambda _, oid=o.id: page.run_task(
                            close_offer_async, oid
                        ),
                    )
                    cells.append(ft.DataCell(close_btn))
                info["table"].rows.append(ft.DataRow(cells=cells))
            info["count"].value = f"{len(subset)} {info['label'].lower()}"

        open_list = [
            o for o in offers if str(getattr(o.status, "value", o.status)) == "OPEN"
        ]
        closed_list = [
            o for o in offers if str(getattr(o.status, "value", o.status)) == "CLOSED"
        ]

        fill(open_group, open_list, with_actions=True)
        fill(closed_group, closed_list)

        page.update()

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

    async def load_offers():
        nonlocal offers
        try:
            loading.visible = True
            page.update()

            offers = await controller.get_offers() or []
            refresh_sections()

            loading.visible = False
            page.update()
        except Exception as e:
            print(f"Error loading offers: {e}")
            offers = controller.get_offers_sync() or []
            refresh_sections()
            loading.visible = False
            show_error("Nie udalo sie zaladowac ofert pracy.")

    async def close_offer_async(offer_id: int):
        try:
            loading.visible = True
            page.update()

            result = await controller.update_offer(offer_id, "", "", "CLOSED")
            if result:
                show_success("Oferta zamknieta")
            else:
                show_error("Nie udalo sie zamknac oferty")

            await load_offers()

            loading.visible = False
            page.update()
        except Exception as e:
            print(f"Error closing offer: {e}")
            loading.visible = False
            show_error("Blad podczas zamykania oferty")

    async def create_offer_async(title, description):
        result = await controller.create_offer(title, description)
        if result:
            show_success("Nowa oferta wystawiona")
        else:
            show_error("Nie udalo sie wystawic oferty")
        await load_offers()

    def post_offer_clicked(e):
        auth_service.update_activity()
        if not title_field.value or not title_field.value.strip():
            show_error("Wypelnij tytul oferty")
            return

        page.run_task(
            create_offer_async,
            title_field.value.strip(),
            description_field.value.strip() if description_field.value else "",
        )

        title_field.value = ""
        description_field.value = ""

    def go_back(e):
        auth_service.update_activity()
        page.clean()
        page.add(create_employees_view(page))
        page.update()

    form = ft.Column(
        controls=[
            ft.Text("Nowa oferta pracy", size=16, weight=ft.FontWeight.BOLD),
            title_field,
            description_field,
            ft.ElevatedButton("Wystaw nowa oferte", on_click=post_offer_clicked),
        ],
        spacing=10,
    )

    content = ft.Column(
        controls=[
            ft.Text("Oferty pracy", size=24, weight=ft.FontWeight.BOLD),
            loading,
            open_group["section"],
            closed_group["section"],
            ft.Divider(),
            form,
            ft.Divider(),
            ft.ElevatedButton(
                "Powrot do menu pracownikow",
                width=400,
                on_click=go_back,
            ),
        ],
        spacing=15,
        scroll=ft.ScrollMode.AUTO,
    )

    page.run_task(load_offers)

    container = ft.Container(
        padding=20,
        content=content,
    )
    container.controls = content.controls
    return container
