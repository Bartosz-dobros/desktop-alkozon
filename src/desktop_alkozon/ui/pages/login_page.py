import flet as ft
from desktop_alkozon.core.logger import setup_logger

class LoginPage(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(
            padding=40,
            alignment=ft.alignment.center,
        )
        self._page = page  
        self.setup_logger = setup_logger
        self.content = ft.Column(
            controls=[
                ft.Text("AlkozOn Desktop", size=32, weight=ft.FontWeight.BOLD),
                ft.Text("Log in to access warehouse, deliveries & employees", size=16),
                ft.Divider(),
                # Username
                ft.TextField(
                    label="Username / Email",
                    width=400,
                    border_radius=8,
                    prefix_icon=ft.icons.PERSON,
                ),
                # Password
                ft.TextField(
                    label="Password",
                    password=True,
                    can_reveal_password=True,
                    width=400,
                    border_radius=8,
                    prefix_icon=ft.icons.LOCK,
                ),
                # Login button
                ft.ElevatedButton(
                    text="LOGIN",
                    width=400,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=self.login_clicked,
                ),
                ft.TextButton("Forgot password?", on_click=lambda e: print("TODO: reset")),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        )

    def login_clicked(self, e):
        """Placeholder – next step connects to core/auth.py + API."""
        self._page.show_snack_bar(
            ft.SnackBar(ft.Text("Login successful (demo)"), duration=2000)
        )
        # TODO: later → call core/auth.py, check 2FA, load dashboard