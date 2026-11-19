import flet as ft
import asyncio
import flet_shadcn_ui as shad


def create_welcome_view(page: ft.Page) -> ft.View:
    ''' Creates a loading view to be shown while the app is initializing '''
    from models.app import app

    async def run_tutorial(e):
        ''' Save that we have launched the app before, and route to the tutorial '''
        progress_ring.visible = True
        progress_ring.update()
        app.settings.update_data(**{'is_first_launch': False})
        await app.settings.save_file()
        await page.push_route("/tutorial")

    async def skip_tutorial(e):
        ''' Save that we have launched the app before, and route to the home view '''
        
        app.settings.update_data(**{'is_first_launch': False})
        await app.settings.save_file()
        await page.push_route("/")
        page.show_dialog(shad.Toast("You can access the tutorial anytime in Settings -> Resources"))

    text = ft.Text(
        "Welcome to Story Board", 
        theme_style="headlineLarge", 
        weight=ft.FontWeight.W_500,
        expand=1,
        opacity=0.00,      # Opacity gets changed in main
        animate_opacity=ft.Animation(5000, ft.AnimationCurve.EASE_IN_OUT),
    )

    run_tutorial_button = shad.Button(
        "Run Tutorial", size=shad.ButtonSize.LG,
        on_click=run_tutorial, variant=shad.ButtonVariant.OUTLINE
    )
    skip_tutorial_button = shad.Button(
        "Skip Tutorial", size=shad.ButtonSize.LG,
        on_click=skip_tutorial, variant=shad.ButtonVariant.OUTLINE
        
    )

    return ft.View(
        route="/welcome",
        controls=[
            ft.Container(expand=4),    # Spacing
            text,
            ft.Row([
                run_tutorial_button,
                
                skip_tutorial_button,
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20, visible=False),
            ft.Text("\nplz run tutorial, I worked really hard on it", visible=False, color=ft.Colors.ON_SURFACE_VARIANT),
            progress_ring := ft.ProgressRing(visible=False),
            ft.Container(expand=4)     # Spacing
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
    )


async def animate_welcome_text(text: ft.Text):
    ''' Animates the welcome text opacity '''
    text.opacity = 1
    text.update()
    await asyncio.sleep(5)    