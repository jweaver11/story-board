import flet as ft

class IsolatedContainer(ft.Container):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def is_isolated(self):
        return True