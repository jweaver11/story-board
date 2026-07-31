import flet as ft
from dataclasses import dataclass, field


# Source of truth. The data for the textcontroller stored here
@ft.observable
@dataclass
class TextController:

    size: int = 14
    weight: str = "normal"  
    italic: bool = False
    decoration: str = "none"  # Options: none, underline, overline,
    decoration_color: str = "#000000"
    decoration_thickness: float = 1.0
    decoration_style: str = "solid"
    font_family: str = "Arial"
    color: str = "#FFFFFF"
    bgcolor: str = "#000000"
    shadow: dict = field(default_factory=lambda: {
        'blur_radius': 0,
        'blur_style': 'normal', # Options: normal, solid, outer, inner
        'color': "black",
        'offset': (0, 0),
        'spread_radius': 0,
    })
    foreground: dict = field(default_factory=lambda: {
        'color': "white",     # Hex color folowed by opacity
        'stroke_width': 3,          # Size of the strokees
        'style': "stroke",          # style of the strokes. Either stroke or fill
        'stroke_cap': "round",      # Each end of the strokes shape
        'stroke_join': "round",     # How corners between strokes are drawn
        'stroke_miter_limit': 10, 
        'stroke_dash_pattern': None,         # If we should use dashed lines, and the pattern for them
        'anti_alias': True,     # Use anti aliasing for smoother strokes or not
        'blur_image': 0,        # How much blur to apply to the stroke
        'blend_mode': None,     # Any blend mode to apply to the stroke, or None for normal
    })   
    letter_spacing: int = 0
    word_spacing: int = 0
    baseline: str = "alphabetic"  # Options: alphabetic, ideographic, hanging, mathematical, central, middle, text-bottom, text-top   

# Essentially the build function for the text controller class, passing in persistant data
@ft.component
def TextControllerView(text_controller: TextController) -> ft.Row:

    settings, set_settings = ft.use_state(text_controller.__dict__)
    bold, set_bold = ft.use_state(text_controller.bold)
    italic, set_italic = ft.use_state(text_controller.italic)

    # Update the data before UI reset
    def update_data():
        from models.app import app
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
