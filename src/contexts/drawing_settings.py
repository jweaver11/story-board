''' Settings for other drawing related stuff that don't fit into ft.paint brush style or ft.textstyle for cv.text '''

import flet as ft
import json
from dataclasses import dataclass, field

@ft.observable
@dataclass
class DrawingSettings:
    control_mode: str = "draw"  # Either "draw", "tools", or "text"
    brush_name: str = "stroke"      # Name of the currently selected brush
    tool_name: str = "erase"        # Current tool or shape being used

    use_brush_smoothing: bool = True         # Uses cv.Path for constistant shapes if true, otherwise use cv.line
    stroke_smoothing_strength: int = 1        # If stroke smoothing is enabled, how strong the smoothing is. 1 = low, 10 = high 0=off
    #saved_brushes: dict = field(default_factory=dict)             # Saved brushes the user has created that we can load
    #saved_colors: list = field(default_factory=list)              # Saved colors the user has created that we can load [{'name': 'name_val', 'value': 'value']
    #saved_text_settings: dict = field(default_factory=dict)          # Saved text settings the user has created that we can load

    rectangle_border_radius: int = 0          # Border radius for rectangle shapes