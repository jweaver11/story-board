import flet as ft

class Card(ft.Container):
    def __init__(self, title: str="", description: str="", content: ft.Control=ft.Container(visible=False), actions: list[ft.Control]=[], **kwargs):

        super().__init__(
            content=ft.Column([
                ft.Text(title, theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, visible=bool(title)),
                ft.Text(description, color=ft.Colors.OUTLINE, margin=ft.Margin.only(bottom=10), visible=bool(description)),
                content,
                ft.Row(actions if actions else [], alignment=ft.MainAxisAlignment.END, tight=True, visible=bool(actions))
            ], tight=True, spacing=0),
            padding=kwargs.pop("padding", ft.Padding.all(20)),
            border_radius=kwargs.pop("border_radius", ft.BorderRadius.all(8)),
            bgcolor=kwargs.pop("bgcolor", ft.Colors.SURFACE),
            **kwargs
        )