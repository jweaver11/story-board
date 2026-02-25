import flet as ft
import asyncio


def create_welcome_view(page: ft.Page) -> ft.View:
    ''' Creates a loading view to be shown while the app is initializing '''
    from models.app import app

    def _run_tutorial_clicked(e):
        ''' Save that we have launched the app before, and route to the tutorial '''
        app.settings.data["is_first_launch"] = False
        app.settings.save_dict()
        #page.route = "/welcome/tutorial"

    def _skip_tutorial_clicked(e):
        ''' Save that we have launched the app before, and route to the home view '''
        app.settings.data["is_first_launch"] = False
        app.settings.save_dict()

    text = ft.Text(
        "Welcome to Story Board", 
        theme_style="headlineLarge", 
        expand=1,
        opacity=0.00,      # Opacity gets changed in main
    )

    run_tutorial_button = ft.Button(
        "Run Tutorial (Recommended)", tooltip="plz I worked really hard on it :(",
        on_click=_run_tutorial_clicked, scale=1.5
    )
    skip_tutorial_button = ft.Button(
        "Skip Tutorial", tooltip="Must be a pro :o", 
        on_click=_skip_tutorial_clicked, scale=1.5
    )

    return ft.View(
        controls=[
            ft.Container(expand=4),    # Spacing
            text,
            ft.Row([
                run_tutorial_button,
                ft.Container(width=75),
                skip_tutorial_button,
            ], alignment=ft.MainAxisAlignment.CENTER, visible=False),
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
        await asyncio.sleep(.04)   # don't block the UI thread; let the animation run