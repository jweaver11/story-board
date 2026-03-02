import flet as ft

class IsolatedTabBarView(ft.Row):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def is_isolated(self) -> bool:
        return True