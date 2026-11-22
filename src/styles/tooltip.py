import flet as ft

@ft.control
class Tooltip(ft.Tooltip):
    def __init__(self, message="", **kwargs):

        super().__init__(
            message=message, 
            bgcolor=ft.Colors.SURFACE,
            wait_duration=kwargs.get("wait_duration", ft.Duration(milliseconds=750)),
            prefer_below=False,
            text_style=ft.TextStyle(color=ft.Colors.ON_SURFACE, size=14),
            decoration=ft.BoxDecoration(
                border_radius=8, 
                #border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                shadows=ft.BoxShadow(2, 4, ft.Colors.SURFACE)
            ),
            size_constraints=ft.BoxConstraints(max_width=300),
            **kwargs
        )

        