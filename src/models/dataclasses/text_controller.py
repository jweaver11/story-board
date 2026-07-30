import flet as ft
from dataclasses import dataclass, field
from models.app import app

# Source of truth. The data for the textcontroller stored here
@ft.observable
@dataclass
class TextController:
    bold: bool = False
    italic: bool = False
    decoration: str = "none"  # Options: none, underline, overline, line-through
    font_size: int = 14
    font_family: str = "Arial"
    letter_spacing: int = 0
    word_spacing: int = 0
    color: str = "#FFFFFF"
    decoration_color: str = "#000000"
    decoration_thickness: float = 1.0
    decoration_style: str = "solid"


@ft.component
def TextControllerView(text_controller: TextController) -> ft.Row:

    settings, set_settings = ft.use_state(text_controller.__dict__)
    bold, set_bold = ft.use_state(text_controller.bold)
    italic, set_italic = ft.use_state(text_controller.italic)

    # Update the data before UI reset
    def update_data():
        set_settings(text_controller.__dict__)
        app.settings.update_data(**{'text_controller_settings': text_controller.__dict__})

    def handle_set_bold(e: ft.Event[ft.IconButton]):
        set_bold(not bold)  
        update_data()
        
    def handle_set_italic(e: ft.Event[ft.IconButton]):
        set_italic(not italic)
        update_data()


    return ft.Row([   

        #ft.Text("Text Controller", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE_VARIANT, size=14, italic=True, opacity=.5),

        ft.IconButton(
            ft.Icons.FORMAT_BOLD,
            ft.Colors.PRIMARY if bold else ft.Colors.ON_SURFACE_VARIANT,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH if bold else ft.Colors.TRANSPARENT,
            data="bold", on_click=handle_set_bold,
            visible=False,  # TEMP
        ),
        ft.IconButton(
            ft.Icons.FORMAT_ITALIC,
            ft.Colors.PRIMARY if italic else ft.Colors.ON_SURFACE_VARIANT,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH if italic else ft.Colors.TRANSPARENT,
            data="italic", on_click=handle_set_italic,
            visible=False,  # TEMP
        ),

        # TODO: Text Controller
        # size, format_align, font family, letter_spacing, word_spacing, color
        # decoration, decoration color, decoration thickness, decoration style
    ], alignment=ft.MainAxisAlignment.CENTER, expand=True, spacing=0)
              