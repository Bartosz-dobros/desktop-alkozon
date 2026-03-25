import flet as ft
import asyncio
from desktop_alkozon.ui.pages.login_page import LoginPage
from desktop_alkozon.core.logger import setup_logger
from desktop_alkozon.core.auth import auth_service   

def main(page: ft.Page):
    page.title = "AlkozOn Desktop"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.window_width = 1200
    page.window_height = 800
    page.window_resizable = True
    page.window_min_width = 800
    page.window_min_height = 600

    login_page = LoginPage(page)
    page.add(login_page)

    setup_logger()

    async def inactivity_checker():
        while True:
            await asyncio.sleep(30)  
            if auth_service.check_inactivity(page):
                snack = ft.SnackBar(
                    content=ft.Text("Wylogowany z powodu braku aktywności."),
                    duration=4000,
                    action="OK"
                )
                page.overlay.append(snack)
                snack.open = True
                page.update()
                page.clean()
                page.add(LoginPage(page))
                page.update()

    page.run_task(inactivity_checker)

if __name__ == "__main__":
    ft.run(main)