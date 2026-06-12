import flet as ft

class TextField(ft.TextField):
    
    def __init__(self, *args, **kwargs):

        

        super().__init__(*args, **kwargs)

        # Default styles
        self.label_style = ft.TextStyle(weight=ft.FontWeight.W_500)
        self.border_color = ft.Colors.OUTLINE_VARIANT
        self.dense = True
        self.border=ft.InputBorder.NONE
        self.content_padding=ft.Padding.all(0)
        self.text_style=ft.TextStyle(size=14)
        self.multiline=True
        self.capitalization=ft.TextCapitalization.SENTENCES
        
        

# Small textfields with no borders
class SmallTextField(TextField):
    
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.label_style = ft.TextStyle(weight=ft.FontWeight.W_500, size=12)
        self.content_padding=ft.Padding.all(0)
        self.text_style=ft.TextStyle(italic=True, color=ft.Colors.ON_SURFACE_VARIANT, size=12)
        self.capitalization=ft.TextCapitalization.SENTENCES
        self.multiline=True
        self.border=ft.InputBorder.NONE
        self.text_align=ft.TextAlign.CENTER