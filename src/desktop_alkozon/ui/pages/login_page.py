import flet as ft
from desktop_alkozon.core.auth import AuthService
from desktop_alkozon.core.logger import setup_logger

class LoginPage(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(
            padding=40,
            alignment=ft.Alignment(0.5, 0.5),
        )
        self._page = page
        self.auth = AuthService()
        self.setup_logger = setup_logger

        self.username_field = ft.TextField(
            label="Username / Email",
            width=400,
            border_radius=8,
            prefix_icon=ft.Icons.PERSON,
            max_length=50,
            text_size=16,
        )
        self.password_field = ft.TextField(
            label="Password",
            password=True,
            can_reveal_password=True,
            width=400,
            border_radius=8,
            prefix_icon=ft.Icons.LOCK,
            max_length=128,
            text_size=16,
        )
        self.two_fa_field = ft.TextField(
            label="2FA Code (6 digits)",
            width=400,
            border_radius=8,
            visible=False,
            max_length=6,
            input_filter=ft.InputFilter(allow=True, regex_string=r"^[0-9]*$"),
            keyboard_type=ft.KeyboardType.NUMBER,
            text_size=16,
        )

        self.login_button = ft.ElevatedButton(
            content=ft.Text("LOGIN"),
            width=400,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            on_click=self.login_clicked,
        )

        self.content = ft.Column(
            controls=[
                ft.Text("AlkozOn Desktop", size=32, weight=ft.FontWeight.BOLD),
                ft.Text("Log in to access warehouse, deliveries & employees", size=16),
                ft.Divider(),
                self.username_field,
                self.password_field,
                self.two_fa_field,
                self.login_button,
                ft.TextButton("Forgot password?", on_click=lambda e: print("TODO: reset")),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        )

    def login_clicked(self, e):
        success = self.auth.login(
            self.username_field.value or "",
            self.password_field.value or "",
            self.two_fa_field.value if self.two_fa_field.visible else None
        )

        if success:
            snack = ft.SnackBar(
                content=ft.Text("Login successful (demo mode)"),
                duration=3000,
                action="OK"
            )
            self._page.overlay.append(snack)
            snack.open = True
            self._page.update()
        else:
            if self.auth.is_locked():
                snack = ft.SnackBar(
                    content=ft.Text("Account locked after 5 failed attempts. Restart the app to try again."),
                    duration=5000,
                    action="OK"
                )
                self.login_button.disabled = True  
            else:
                remaining = max(0, 5 - self.auth.attempts)
                snack = ft.SnackBar(
                    content=ft.Text(f"Login failed. Attempts left: {remaining}"),
                    duration=3000,
                    action="OK"
                )

            self._page.overlay.append(snack)
            snack.open = True
            self._page.update()

            if self.auth.attempts >= 3 and not self.auth.is_locked():
                self.two_fa_field.visible = True
                self._page.update()