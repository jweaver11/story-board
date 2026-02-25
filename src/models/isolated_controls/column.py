''' Simple Isolated Column control so when we update, we don't overdo it with hundreds/thousands of unnecessary updates to controls inside '''

import flet as ft

class IsolatedColumn(ft.Column):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def is_isolated(self) -> bool:
        return True