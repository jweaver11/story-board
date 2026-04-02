import flet as ft

class TextField(ft.TextField):
    

    def __init__(self, *args, **kwargs):
        
        super().__init__(*args, **kwargs)

        self.label_style = ft.TextStyle(weight=ft.FontWeight.BOLD)
        self.border_color = ft.Colors.OUTLINE_VARIANT
        self.dense = True
