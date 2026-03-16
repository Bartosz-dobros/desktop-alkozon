import flet as ft
from desktop_alkozon.ui.pages.login_page import LoginPage
from desktop_alkozon.core.logger import setup_logger

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

if __name__ == "__main__":
    ft.run(main)  