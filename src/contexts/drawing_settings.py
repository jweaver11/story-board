''' Settings for other drawing related stuff that don't fit into ft.paint brush style or ft.textstyle for cv.text '''

import flet as ft
import json
import os
from dataclasses import asdict
from dataclasses import dataclass, field, fields
from contexts.constants import APP_DATA_PATH, DRAWING_SETTINGS_FILE_PATH
 
@ft.observable
@dataclass
class DrawingSettings:
    control_mode: str = "draw"  # Either "draw", "tools", or "text"
    brush_name: str = "stroke"      # Name of the currently selected brush
    tool_name: str = "erase"        # Current tool or shape being used

    use_brush_smoothing: bool = True         # Uses cv.Path for constistant shapes if true, otherwise use cv.line
    stroke_smoothing_strength: int = 1        # If stroke smoothing is enabled, how strong the smoothing is. 1 = low, 10 = high 0=off
    saved_brushes: dict[str, dict] = field(default_factory=dict)             # Saved brushes the user has created that we can load
    saved_colors: dict[str, str] = field(default_factory=dict)              # Saved colors the user has created that we can load [{'name': 'name_val', 'value': 'value']
    saved_text_settings: dict[str, dict] = field(default_factory=dict)          # Saved text settings the user has created that we can load

    rectangle_border_radius: int = 0          # Border radius for rectangle shapes

    # Called whenever there are changes in our data
    async def save_file(self):
        ''' Saves our current data to the json file '''

        try:
            
            os.makedirs(APP_DATA_PATH, exist_ok=True)
            drawing_data = {
                drawing_field.name: getattr(self, drawing_field.name)
                for drawing_field in fields(self)
            }
            # Save the data to the file (creates file if doesnt exist)
            with open(DRAWING_SETTINGS_FILE_PATH, "w", encoding='utf-8') as f:   
                json.dump(drawing_data, f, indent=4)   # asdict() strips observable bookkeeping, unlike self.__dict__
        
        except Exception as e:
            print(f"Error saving settings to {DRAWING_SETTINGS_FILE_PATH}: {e}")