''' View for our tutorial page '''
import flet as ft
import asyncio


def create_tutorial_view(page: ft.Page) -> ft.View:
    from models.app import app

    return ft.View(
        route="/tutorial",
        controls=[
            
        ],
    )