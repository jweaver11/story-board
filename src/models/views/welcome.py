import flet as ft
import asyncio
from styles.snack_bar import SnackBar


def create_welcome_view(page: ft.Page) -> ft.View:
    ''' Creates a loading view to be shown while the app is initializing '''
    from models.app import app

    async def _run_tutorial_clicked(e):
        ''' Save that we have launched the app before, and route to the tutorial '''
        progress_ring.visible = True
        progress_ring.update()
        await asyncio.sleep(0.5)
        app.settings.data["is_first_launch"] = False
        await app.settings.save_dict()
        await page.push_route("/tutorial")

    async def _skip_tutorial_clicked(e):
        ''' Save that we have launched the app before, and route to the home view '''
        app.settings.data["is_first_launch"] = False
        await app.settings.save_dict()
        page.show_dialog(SnackBar("You can access the tutorial anytime in Settings -> Resources", duration=7000))

    text = ft.Text(
        "Welcome to Story Board", 
        theme_style="headlineLarge", 
        expand=1,
        opacity=0.00,      # Opacity gets changed in main
    )

    run_tutorial_button = ft.Button(
        "Run Tutorial", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
        on_click=_run_tutorial_clicked, scale=1.5
    )
    skip_tutorial_button = ft.Button(
        "Skip Tutorial", tooltip="Must be a pro :o", 
        on_click=_skip_tutorial_clicked, scale=1.5,
        style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
    )

    return ft.View(
        route="/welcome",
        controls=[
            ft.Container(expand=4),    # Spacing
            text,
            ft.Row([
                run_tutorial_button,
                ft.Container(width=75),
                skip_tutorial_button,
            ], alignment=ft.MainAxisAlignment.CENTER, visible=False),
            ft.Text("plz run tutorial, I worked really hard on it", visible=False, color=ft.Colors.ON_SURFACE_VARIANT),
            progress_ring := ft.ProgressRing(visible=False),
            ft.Container(expand=4)     # Spacing
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10,
    )


async def animate_welcome_text(text: ft.Text):
    ''' Animates the welcome text opacity '''
    while text.opacity < 1.0:
        text.opacity += round(0.01, 2)
        if text.opacity >= 0.99:
            text.opacity = 1.0

        text.update()
        # TEMP
        await asyncio.sleep(.04)   # don't block the UI thread; let the animation run
        #await asyncio.sleep(.001)