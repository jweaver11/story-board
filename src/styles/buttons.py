import flet as ft


class PopupMenuButton(ft.PopupMenuButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.menu_padding = 4
        self.menu_position = ft.PopupMenuPosition.OVER
        self.popup_animation_style = ft.AnimationStyle(
            ft.Duration(milliseconds=200),
            ft.Duration(milliseconds=200),
            ft.AnimationCurve.DECELERATE, 
            ft.AnimationCurve.DECELERATE
        )

class PopupMenuItem(ft.PopupMenuItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.height = 24
        self.padding = ft.Padding.symmetric(vertical=2, horizontal=4)
        self.mouse_cursor = ft.MouseCursor.CLICK
