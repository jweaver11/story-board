''' Class and data for all our text options for canvases '''

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
