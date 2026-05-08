import asyncio
import flet as ft
from .client_view import ClientView
from .server_view import ServerView
from .config import Config

async def main(page: ft.Page):
    page.title = "cmdbroker"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.spacing = 0

    config = Config()

    client_view = ClientView(page, config)
    server_view = ServerView(page, config)

    def on_nav_change(e):
        index = e.control.selected_index
        client_view.visible = (index == 0)
        server_view.visible = (index == 1)
        page.update()

    page.navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.icons.Icons.TERMINAL, label="Client"),
            ft.NavigationBarDestination(icon=ft.icons.Icons.DASHBOARD, label="Server"),
        ],
        on_change=on_nav_change,
    )

    page.add(
        ft.Column(
            [
                client_view,
                server_view,
            ],
            expand=True,
        )
    )

    # Initial state
    client_view.visible = True
    server_view.visible = False
    page.update()

def run_gui():
    ft.app(target=main)
