import asyncio
import logging
import sys

import flet as ft

from desktop_alkozon.core.auth import auth_service
from desktop_alkozon.core.database import init_db
from desktop_alkozon.core.i18n import load_language
from desktop_alkozon.core.logger import setup_logger
from desktop_alkozon.ui.pages.login_page import (
    create_hard_lockout_view,
    create_login_page_view,
)

logger = logging.getLogger("desktop_alkozon")


def excepthook(exc_type, exc_value, exc_tb):
    logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_tb))


sys.excepthook = excepthook


def main(page: ft.Page):
    page.title = "AlkozOn Desktop"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.window_width = 1200
    page.window_height = 800
    page.window_resizable = True
    page.window_min_width = 800
    page.window_min_height = 600

    setup_logger()

    async def start_app():
        await init_db()
        await load_language(page)
        if await auth_service.is_hard_locked():
            page.add(create_hard_lockout_view(page))
        else:
            page.add(create_login_page_view(page))
        page.update()

    page.run_task(start_app)

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
