import flet as ft
import asyncio


def create_welcome_view(page: ft.Page) -> ft.View:
    ''' Creates a loading view to be shown while the app is initializing '''

    text = ft.Text(
        "Welcome to Story Board", 
        theme_style="headlineLarge", 
        expand=1,
        opacity=0,      # Opacity gets changed in main
    )

    return ft.View(
        controls=[
            ft.Container(expand=4),    # Spacing
            text,
            ft.ProgressRing(opacity=0),
            ft.Container(expand=4)     # Spacing
        ],
        route="/welcome",
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        vertical_alignment=ft.MainAxisAlignment.START,
    )


async def animate_welcome_text(text: ft.Text):
    ''' Animates the welcome text opacity '''
    while text.opacity < 1.0:
        text.opacity += round(0.01, 2)
        if text.opacity >= 0.99:
            text.opacity = 1.0

        text.update()
        await asyncio.sleep(.05)   # don't block the UI thread; let the animation run