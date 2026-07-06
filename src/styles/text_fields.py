import flet as ft

# Standard styling for most text fields we use
class TextField(ft.TextField):
    
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # Default styles
        self.label_style = ft.TextStyle(weight=ft.FontWeight.BOLD, italic=True, size=16, color=ft.Colors.PRIMARY)
        self.dense = True
        self.border=ft.InputBorder.NONE
        self.content_padding=ft.Padding.only(left=0, top=0, right=0, bottom=12)
        self.text_style=ft.TextStyle(size=14)
        self.multiline=True
        self.capitalization=ft.TextCapitalization.SENTENCES
        self.bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST

# Meant to be used with no label
class NoLabelTextField(TextField):
    
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.dense = True
        self.border=ft.InputBorder.NONE
        self.text_style=ft.TextStyle(size=14)
        self.multiline=True
        self.content_padding=ft.Padding.all(0)
        self.capitalization=ft.TextCapitalization.SENTENCES
        self.bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST
        
# Underlined Text Fields
class UnderlinedTextField(TextField):
    
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.border=ft.InputBorder.UNDERLINE
        self.border_color=ft.Colors.BLACK
        self.border_width=1
        self.label_style = ft.TextStyle(weight=ft.FontWeight.W_500, size=16)
        self.dense = True
        
        self.text_style=ft.TextStyle(size=14)
        self.multiline=True
        self.capitalization=ft.TextCapitalization.SENTENCES
        self.bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST
        
# Small textfields
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
        self.bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST