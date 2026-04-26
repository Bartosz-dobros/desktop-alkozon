import flet as ft
import asyncio
from desktop_alkozon.ui.pages.login_page import create_login_page_view
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

    page.add(create_login_page_view(page))

    setup_logger()

    async def inactivity_checker():
        while True:
            await asyncio.sleep(30)  
            if auth_service.is_authenticated():
                should_logout = await auth_service.check_inactivity(page)
                if should_logout:
                    auth_service.logout()
                    page.clean()
                    page.add(create_login_page_view(page))
                    page.update()

    page.run_task(inactivity_checker)

if __name__ == "__main__":
    ft.run(main)
