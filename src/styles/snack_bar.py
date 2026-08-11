import flet as ft


# Give uniform styling to our snack bars
class SnackBar(ft.SnackBar):

    # Constructor
    def __init__(self, error_text: str, duration: int=None):

        # Parent constructor
        super().__init__(
            content=ft.Container(
                ft.Text(error_text, theme_style=ft.TextThemeStyle.BODY_LARGE, color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, expand=True),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                border_radius=4,
                border=ft.Border.only(
                    top=ft.BorderSide(2, ft.Colors.PRIMARY),
                    #left=ft.BorderSide(2, ft.Colors.ERROR),
                    #right=ft.BorderSide(2, ft.Colors.ERROR),
                ),
                padding=ft.Padding.symmetric(horizontal=20, vertical=14)
            ),
            duration=duration,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            padding=ft.Padding.all(0)
        )
        