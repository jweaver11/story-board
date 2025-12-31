import flet as ft


# Give uniform styling to our snack bars
class SnackBar(ft.SnackBar):

    # Constructor
    def __init__(self, error_text: str):

        # Parent constructor
        super().__init__(
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            content=ft.Text(error_text, theme_style=ft.TextThemeStyle.BODY_LARGE, color=ft.Colors.ON_SURFACE, expand=True),
            padding=None,
            shape=ft.RoundedRectangleBorder(radius=8),
        )
        