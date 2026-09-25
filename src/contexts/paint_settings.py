import flet as ft
import json
from dataclasses import dataclass, field, asdict
import os
from contexts.constants import APP_DATA_PATH, PAINT_SETTINGS_FILE_PATH

@ft.observable
@dataclass 
class PaintSettings:
    color: str = "#FFFFFFFF"     # Hex color folowed by opacity
    stroke_width: int = 3          # Size of the strokees
    style: str = "stroke"          # style of the strokes. Either stroke or fill
    stroke_cap: str = "round"      # Each end of the strokes shape
    stroke_join: str = "round"     # How corners between strokes are drawn
    stroke_miter_limit: int = 10
    stroke_dash_pattern: list = None         # If we should use dashed lines, and the pattern for them
    anti_alias: bool = True     # Use anti aliasing for smoother strokes or not
    blur_image: int = 0        # How much blur to apply to the stroke
    blend_mode: str = None     # Any blend mode to apply to the stroke, or None for normal

    async def save_file(self):
        ''' Saves our current data to the json file '''

        try:
            os.makedirs(APP_DATA_PATH, exist_ok=True)
            # Save the data to the file (creates file if doesnt exist)
            with open(PAINT_SETTINGS_FILE_PATH, "w", encoding='utf-8') as f:   
                json.dump(asdict(self), f, indent=4)   # asdict() strips observable bookkeeping, unlike self.__dict__
        
        except Exception as e:
            print(f"Error saving settings to {PAINT_SETTINGS_FILE_PATH}: {e}")
