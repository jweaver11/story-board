import flet as ft

@ft.control
class HighlightButton(ft.GestureDetector):
    def __init__(self, content=None, on_tap=None, is_round=False, use_padding=False, **kwargs):
        super().__init__(
            content=ft.Container(content=content, border_radius=6, shape=ft.BoxShape.CIRCLE if is_round else ft.BoxShape.RECTANGLE, padding=8 if use_padding else None), 
            on_tap=on_tap, 
            on_enter=self.highlight,
            on_exit=self.unhighlight,
            **kwargs
        )

    def highlight(self, e=None):
        self.content.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE)
        self.content.update()
    def unhighlight(self, e=None):
        self.content.bgcolor = None
        self.content.update()

    